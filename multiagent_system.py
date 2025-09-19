import json
import sqlite3
import datetime
import os
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import requests
import PyPDF2
from email.parser import Parser
from email.policy import default

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Standard result format for all agents"""
    success: bool
    data: Dict[str, Any]
    agent_type: str
    classification: Dict[str, str]
    timestamp: str
    thread_id: str
    errors: list = None

class SharedMemory:
    """Lightweight shared memory using SQLite"""
    
    def __init__(self, db_path: str = "shared_memory.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT,
                source_type TEXT,
                intent TEXT,
                timestamp TEXT,
                agent_type TEXT,
                extracted_data TEXT,
                status TEXT,
                errors TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_store (
                thread_id TEXT PRIMARY KEY,
                sender TEXT,
                topic TEXT,
                last_extracted_fields TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_processing(self, result: ProcessingResult):
        """Log processing result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO processing_logs 
            (thread_id, source_type, intent, timestamp, agent_type, extracted_data, status, errors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.thread_id,
            result.classification.get('format', ''),
            result.classification.get('intent', ''),
            result.timestamp,
            result.agent_type,
            json.dumps(result.data),
            'success' if result.success else 'failed',
            json.dumps(result.errors or [])
        ))
        
        conn.commit()
        conn.close()
    
    def update_context(self, thread_id: str, sender: str = None, topic: str = None, 
                      extracted_fields: Dict = None):
        """Update shared context for a thread"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()     
        now = datetime.datetime.now().isoformat()
        cursor.execute('SELECT thread_id FROM context_store WHERE thread_id = ?', (thread_id,))
        exists = cursor.fetchone()
        
        if exists:
            updates = []
            params = []
            
            if sender:
                updates.append('sender = ?')
                params.append(sender)
            if topic:
                updates.append('topic = ?')
                params.append(topic)
            if extracted_fields:
                updates.append('last_extracted_fields = ?')
                params.append(json.dumps(extracted_fields))
            
            updates.append('updated_at = ?')
            params.append(now)
            params.append(thread_id)
            
            cursor.execute(f'''
                UPDATE context_store SET {', '.join(updates)}
                WHERE thread_id = ?
            ''', params)
        else:
            cursor.execute('''
                INSERT INTO context_store 
                (thread_id, sender, topic, last_extracted_fields, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                thread_id,
                sender or '',
                topic or '',
                json.dumps(extracted_fields or {}),
                now,
                now
            ))
        
        conn.commit()
        conn.close()
    
    def get_context(self, thread_id: str) -> Dict:
        """Get context for a thread"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sender, topic, last_extracted_fields, created_at, updated_at
            FROM context_store WHERE thread_id = ?
        ''', (thread_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'sender': result[0],
                'topic': result[1],
                'last_extracted_fields': json.loads(result[2]) if result[2] else {},
                'created_at': result[3],
                'updated_at': result[4]
            }
        return {}

class LLMClient:
    """OpenRouter API client"""
    
    def __init__(self, api_key: str):
        self.api_key = "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"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def call(self, messages: list, model: str = "meta-llama/llama-3.1-8b-instruct:free") -> str:
        """Make API call to OpenRouter"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return f"Error: {str(e)}"

class ClassifierAgent:
    """Central classifier that routes inputs to appropriate agents"""
    
    def __init__(self, llm_client: LLMClient, shared_memory: SharedMemory):
        self.llm_client = llm_client
        self.shared_memory = shared_memory
    
    def classify(self, content: str, filename: str = "", thread_id: str = None) -> Dict[str, str]:
        """Classify input format and intent"""
        format_type = self._detect_format(content, filename)
        intent_prompt = f"""
        Analyze the following content and classify its intent. Choose from:
        - Invoice: Bills, payment requests, receipts
        - RFQ: Request for Quote, procurement requests  
        - Complaint: Customer complaints, issues, feedback
        - Regulation: Legal documents, compliance, policies
        - General: Other business communications
        
        Content preview: {content[:500]}...
        
        Respond with only the intent category (Invoice/RFQ/Complaint/Regulation/General):
        """
        
        messages = [{"role": "user", "content": intent_prompt}]
        intent = self.llm_client.call(messages).strip()
        
        classification = {
            "format": format_type,
            "intent": intent,
            "confidence": "high" if len(content) > 100 else "medium"
        }
        if thread_id:
            self.shared_memory.log_processing(ProcessingResult(
                success=True,
                data={"classification": classification},
                agent_type="classifier",
                classification=classification,
                timestamp=datetime.datetime.now().isoformat(),
                thread_id=thread_id
            ))
        
        return classification
    
    def _detect_format(self, content: str, filename: str) -> str:
        """Detect input format"""
        filename = filename.lower()
        
        if filename.endswith('.pdf') or 'PDF' in content[:100]:
            return "PDF"
        elif filename.endswith('.json') or content.strip().startswith('{'):
            return "JSON"
        elif 'From:' in content or 'Subject:' in content or '@' in content:
            return "Email"
        else:
            return "Text"
    
    def route(self, content: str, filename: str = "", thread_id: str = None) -> Tuple[str, Dict]:
        """Classify and route to appropriate agent"""
        classification = self.classify(content, filename, thread_id)
        
        agent_mapping = {
            "JSON": "json_agent",
            "Email": "email_agent", 
            "PDF": "pdf_agent",
            "Text": "email_agent"
        }
        
        target_agent = agent_mapping.get(classification["format"], "email_agent")
        
        return target_agent, classification

class JSONAgent:
    """Agent for processing JSON payloads"""
    
    def __init__(self, llm_client: LLMClient, shared_memory: SharedMemory):
        self.llm_client = llm_client
        self.shared_memory = shared_memory
    
    def process(self, content: str, classification: Dict, thread_id: str) -> ProcessingResult:
        """Process JSON input"""
        try:
            data = json.loads(content)
            
            target_schema = self._get_target_schema(classification["intent"])
            extracted = self._extract_to_schema(data, target_schema)
            anomalies = self._detect_anomalies(extracted, target_schema)
            
            result_data = {
                "original_data": data,
                "extracted_data": extracted,
                "anomalies": anomalies,
                "schema_compliance": len(anomalies) == 0
            }
            self.shared_memory.update_context(
                thread_id=thread_id,
                extracted_fields=extracted
            )
            
            return ProcessingResult(
                success=True,
                data=result_data,
                agent_type="json_agent",
                classification=classification,
                timestamp=datetime.datetime.now().isoformat(),
                thread_id=thread_id
            )
            
        except json.JSONDecodeError as e:
            return ProcessingResult(
                success=False,
                data={},
                agent_type="json_agent", 
                classification=classification,
                timestamp=datetime.datetime.now().isoformat(),
                thread_id=thread_id,
                errors=[f"JSON parsing error: {str(e)}"]
            )
        except Exception as e:
            return ProcessingResult(
                success=False,
                data={},
                agent_type="json_agent",
                classification=classification, 
                timestamp=datetime.datetime.now().isoformat(),
                thread_id=thread_id,
                errors=[f"Processing error: {str(e)}"]
            )
    
    def _get_target_schema(self, intent: str) -> Dict:
        """Get target schema based on intent"""
        schemas = {
            "Invoice": {
                "required": ["invoice_number", "amount", "date", "vendor"],
                "optional": ["due_date", "items", "tax_amount"]
            },
            "RFQ": {
                "required": ["rfq_number", "items", "deadline", "contact"],
                "optional": ["specifications", "budget_range"]
            },
            "Complaint": {
                "required": ["issue_type", "description", "severity"],
                "optional": ["customer_id", "product_id", "date_occurred"]
            }
        }
        return schemas.get(intent, {
            "required": ["type", "description"],
            "optional": ["metadata"]
        })
    
    def _extract_to_schema(self, data: Dict, schema: Dict) -> Dict:
        """Extract data according to target schema"""
        extracted = {}
        prompt = f"""
        Extract the following fields from this JSON data:
        Required fields: {schema.get('required', [])}
        Optional fields: {schema.get('optional', [])}
        
        Source data: {json.dumps(data, indent=2)}
        
        Return a JSON object with the extracted fields. If a required field is missing, set it to null.
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm_client.call(messages)
        
        try:
            extracted = json.loads(response)
        except:
            all_fields = schema.get('required', []) + schema.get('optional', [])
            for field in all_fields:
                if field in data:
                    extracted[field] = data[field]
                else:
                    for key in data.keys():
                        if field.lower() in key.lower() or key.lower() in field.lower():
                            extracted[field] = data[key]
                            break
        
        return extracted
    
    def _detect_anomalies(self, extracted: Dict, schema: Dict) -> list:
        """Detect anomalies or missing required fields"""
        anomalies = []
        for field in schema.get('required', []):
            if field not in extracted or extracted[field] is None:
                anomalies.append(f"Missing required field: {field}")
        for field, value in extracted.items():
            if 'amount' in field.lower() or 'price' in field.lower():
                try:
                    float(str(value).replace('$', '').replace(',', ''))
                except:
                    anomalies.append(f"Invalid numeric format for {field}: {value}")
            
            if 'date' in field.lower():
                if not self._is_valid_date(str(value)):
                    anomalies.append(f"Invalid date format for {field}: {value}")
        
        return anomalies
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if string is a valid date"""
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
        for fmt in date_formats:
            try:
                datetime.datetime.strptime(date_str, fmt)
                return True
            except:
                continue
        return False

class EmailAgent:
    """Agent for processing email content"""
    
    def __init__(self, llm_client: LLMClient, shared_memory: SharedMemory):
        self.llm_client = llm_client
        self.shared_memory = shared_memory
    
    def process(self, content: str, classification: Dict, thread_id: str) -> ProcessingResult:
        """Process email input"""
        try:
            email_data = self._parse_email(content)
            extracted = self._extract_email_info(email_data, classification)
            urgency = self._assess_urgency(email_data["body"])
            crm_formatted = self._format_for_crm(extracted, urgency)
            
            result_data = {
                "email_structure": email_data,
                "extracted_info": extracted,
                "urgency_level": urgency,
                "crm_formatted": crm_formatted
            }
            self.shared_memory.update_context(
                thread_id=thread_id,
                sender=extracted.get("sender", ""),
                topic=extracted.get("subject", ""),
                extracted_fields=extracted
            )
            
            return ProcessingResult(
                success=True,
                data=result_data,
                agent_type="email_agent",
                classification=classification,
                timestamp=datetime.datetime.now().isoformat(),
                thread_id=thread_id
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                data={},
                agent_type="email_agent",
                classification=classification,
                timestamp=datetime.datetime.now().isoformat(),
                thread_id=thread_id,
                errors=[f"Email processing error: {str(e)}"]
            )
    
    def _parse_email(self, content: str) -> Dict:
        """Parse email structure"""
        try:
            msg = Parser(policy=default).parsestr(content)
            
            return {
                "from": msg.get("From", ""),
                "to": msg.get("To", ""),
                "subject": msg.get("Subject", ""),
                "date": msg.get("Date", ""),
                "body": msg.get_payload() if msg.is_multipart() else str(msg.get_payload())
            }
        except:
            lines = content.split('\n')
            email_data = {
                "from": "",
                "to": "",
                "subject": "",
                "date": "",
                "body": content
            }
            
            for line in lines[:10]:
                if line.startswith("From:"):
                    email_data["from"] = line[5:].strip()
                elif line.startswith("To:"):
                    email_data["to"] = line[3:].strip()
                elif line.startswith("Subject:"):
                    email_data["subject"] = line[8:].strip()
                elif line.startswith("Date:"):
                    email_data["date"] = line[5:].strip()
            
            return email_data
    
    def _extract_email_info(self, email_data: Dict, classification: Dict) -> Dict:
        """Extract key information using LLM"""
        
        prompt = f"""
        Extract key information from this email based on its classification as "{classification['intent']}":
        
        From: {email_data['from']}
        Subject: {email_data['subject']}
        Body: {email_data['body'][:1000]}...
        
        Extract the following information and return as JSON:
        {{
            "sender": "sender name and email",
            "sender_company": "company name if mentioned",
            "subject": "email subject",
            "key_points": ["list of main points"],
            "action_items": ["specific actions requested"],
            "entities": ["people, companies, products mentioned"],
            "sentiment": "positive/negative/neutral",
            "intent_specific": {{
                // Intent-specific fields based on classification
            }}
        }}
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm_client.call(messages)
        
        try:
            extracted = json.loads(response)
        except:
            extracted = {
                "sender": email_data["from"],
                "subject": email_data["subject"],
                "key_points": [email_data["body"][:200] + "..."],
                "action_items": [],
                "entities": [],
                "sentiment": "neutral"
            }
        
        return extracted
    
    def _assess_urgency(self, body: str) -> str:
        """Assess email urgency"""
        urgency_keywords = {
            "high": ["urgent", "asap", "immediately", "emergency", "critical", "deadline"],
            "medium": ["soon", "priority", "important", "needed", "required"],
            "low": ["when possible", "no rush", "fyi", "update"]
        }
        
        body_lower = body.lower()
        
        for level, keywords in urgency_keywords.items():
            if any(keyword in body_lower for keyword in keywords):
                return level
        
        return "medium"
    
    def _format_for_crm(self, extracted: Dict, urgency: str) -> Dict:
        """Format extracted data for CRM system"""
        return {
            "contact_name": extracted.get("sender", ""),
            "company": extracted.get("sender_company", ""),
            "subject": extracted.get("subject", ""),
            "priority": urgency,
            "category": extracted.get("sentiment", "neutral"),
            "summary": " | ".join(extracted.get("key_points", [])),
            "next_actions": extracted.get("action_items", []),
            "created_date": datetime.datetime.now().isoformat(),
            "status": "new"
        }

class MultiAgentSystem:
    """Main orchestrator for the multi-agent system"""
    
    def __init__(self, api_key: str):
        self.shared_memory = SharedMemory()
        self.llm_client = LLMClient(api_key)
        self.classifier = ClassifierAgent(self.llm_client, self.shared_memory)
        self.json_agent = JSONAgent(self.llm_client, self.shared_memory)
        self.email_agent = EmailAgent(self.llm_client, self.shared_memory)
        
        self.agents = {
            "json_agent": self.json_agent,
            "email_agent": self.email_agent,
            "pdf_agent": self.email_agent  
        }
    
    def process_input(self, content: str, filename: str = "", thread_id: str = None) -> ProcessingResult:
        """Main processing pipeline"""
        
        if not thread_id:
            thread_id = f"thread_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Processing input - Thread: {thread_id}, File: {filename}")
        
        try:
            target_agent, classification = self.classifier.route(content, filename, thread_id)
            
            logger.info(f"Classified as {classification['format']} with intent {classification['intent']}")
            logger.info(f"Routing to {target_agent}")
            agent = self.agents[target_agent]
            result = agent.process(content, classification, thread_id)
            self.shared_memory.log_processing(result)
            
            logger.info(f"Processing {'completed' if result.success else 'failed'}")
            
            return result
            
        except Exception as e:
            logger.error(f"System error: {e}")
            return ProcessingResult(
                success=False,
                data={},
                agent_type="system",
                classification={"format": "unknown", "intent": "unknown"},
                timestamp=datetime.datetime.now().isoformat(),
                thread_id=thread_id,
                errors=[f"System error: {str(e)}"]
            )
    
    def process_file(self, file_path: str, thread_id: str = None) -> ProcessingResult:
        """Process file input"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return ProcessingResult(
                success=False,
                data={},
                agent_type="system",
                classification={"format": "unknown", "intent": "unknown"},
                timestamp=datetime.datetime.now().isoformat(),
                thread_id=thread_id or "unknown",
                errors=[f"File not found: {file_path}"]
            )
        try:
            if file_path.suffix.lower() == '.pdf':
                content = self._read_pdf(file_path)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            return self.process_input(content, file_path.name, thread_id)
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                data={},
                agent_type="system",
                classification={"format": "unknown", "intent": "unknown"},
                timestamp=datetime.datetime.now().isoformat(),
                thread_id=thread_id or "unknown",
                errors=[f"File reading error: {str(e)}"]
            )
    
    def _read_pdf(self, file_path: Path) -> str:
        """Extract text from PDF"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            return f"PDF reading error: {str(e)}"
    
    def get_context(self, thread_id: str) -> Dict:
        """Get shared context for a thread"""
        return self.shared_memory.get_context(thread_id)
    
    def get_processing_history(self, thread_id: str = None) -> list:
        """Get processing history"""
        conn = sqlite3.connect(self.shared_memory.db_path)
        cursor = conn.cursor()
        
        if thread_id:
            cursor.execute('''
                SELECT * FROM processing_logs WHERE thread_id = ?
                ORDER BY timestamp DESC
            ''', (thread_id,))
        else:
            cursor.execute('''
                SELECT * FROM processing_logs 
                ORDER BY timestamp DESC LIMIT 50
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(zip([col[0] for col in cursor.description], row)) for row in results]

def main():
    """Demo function"""
    API_KEY = os.getenv("OPENROUTER_API_KEY", "your-api-key-here")
    
    if API_KEY == "your-api-key-here":
        print("Please set your OpenRouter API key in the OPENROUTER_API_KEY environment variable")
        return
    system = MultiAgentSystem(API_KEY)
    print("=== Multi-Agent AI System Demo ===\n")

    json_invoice = '''
    {
        "document_type": "invoice",
        "invoice_id": "INV-2024-001",
        "vendor": "Tech Solutions Inc",
        "amount": 1250.00,
        "date": "2024-01-15",
        "items": [
            {"description": "Software License", "quantity": 1, "price": 1000.00},
            {"description": "Support", "quantity": 1, "price": 250.00}
        ]
    }
    '''
    
    print("1. Processing JSON Invoice...")
    result1 = system.process_input(json_invoice, "invoice.json", "demo_thread_1")
    print(f"Success: {result1.success}")
    print(f"Agent: {result1.agent_type}")
    print(f"Classification: {result1.classification}")
    if result1.success:
        print(f"Extracted: {result1.data.get('extracted_data', {})}")
    print()
    email_rfq = '''
    From: john.doe@company.com
    To: procurement@ourcompany.com
    Subject: RFQ for Office Furniture - Urgent
    Date: Mon, 15 Jan 2024 10:30:00 +0000
    
    Dear Procurement Team,
    
    We need quotes for the following office furniture:
    - 50 ergonomic office chairs
    - 25 standing desks
    - 10 conference tables
    
    Our budget is around $75,000 and we need delivery by March 1st.
    This is urgent as we're expanding our team rapidly.
    
    Please send detailed quotes ASAP.
    
    Best regards,
    John Doe
    '''
    
    print("2. Processing Email RFQ...")
    result2 = system.process_input(email_rfq, "rfq_email.txt", "demo_thread_2")
    print(f"Success: {result2.success}")
    print(f"Agent: {result2.agent_type}")
    print(f"Classification: {result2.classification}")
    if result2.success:
        print(f"Urgency: {result2.data.get('urgency_level', 'unknown')}")
        print(f"CRM Format: {result2.data.get('crm_formatted', {})}")
    print()
    print("3. Processing History:")
    history = system.get_processing_history()
    for entry in history[:3]:
        print(f"  {entry['timestamp']}: {entry['agent_type']} - {entry['source_type']}/{entry['intent']} - {entry['status']}")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":

    main()
