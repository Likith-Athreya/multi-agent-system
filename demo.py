"""
Interactive Demo Script for Multi-Agent AI System
Run this script to test the system with various inputs
"""

import os
import json
from pathlib import Path
from multiagent_system import MultiAgentSystem

def create_sample_files():
    """Create sample input files for testing"""
    
    # Create samples directory
    samples_dir = Path("sample_inputs")
    samples_dir.mkdir(exist_ok=True)
    
    # Sample JSON Invoice
    json_invoice = {
        "document_type": "invoice",
        "invoice_number": "INV-2024-001",
        "vendor": "TechCorp Solutions",
        "amount": 2500.75,
        "currency": "USD",
        "issue_date": "2024-01-15",
        "due_date": "2024-02-15",
        "client": {
            "name": "ABC Corporation",
            "address": "123 Business St, Tech City, TC 12345"
        },
        "items": [
            {
                "description": "AI Development Services",
                "quantity": 40,
                "unit_price": 50.00,
                "total": 2000.00
            },
            {
                "description": "System Integration",
                "quantity": 1,
                "unit_price": 500.75,
                "total": 500.75
            }
        ],
        "tax_rate": 0.08,
        "tax_amount": 200.06,
        "total_amount": 2500.75
    }
    
    with open(samples_dir / "sample_invoice.json", "w") as f:
        json.dump(json_invoice, f, indent=2)
    
    # Sample JSON RFQ
    json_rfq = {
        "document_type": "rfq",
        "rfq_number": "RFQ-2024-005",
        "company": "Global Manufacturing Inc",
        "contact": {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@globalmanuf.com",
            "phone": "+1-555-0123"
        },
        "deadline": "2024-02-28",
        "budget_range": "$50,000 - $100,000",
        "items_requested": [
            {
                "category": "Industrial Equipment",
                "description": "Heavy-duty conveyor belt system",
                "quantity": 3,
                "specifications": {
                    "length": "50 meters",
                    "capacity": "500kg/hour",
                    "material": "Food-grade stainless steel"
                }
            },
            {
                "category": "Installation Services",
                "description": "Professional installation and setup",
                "quantity": 1,
                "specifications": {
                    "timeline": "Within 2 weeks of delivery",
                    "training": "4 hours operator training included"
                }
            }
        ],
        "requirements": [
            "ISO 9001 certification required",
            "2-year warranty minimum",
            "24/7 support availability"
        ]
    }
    
    with open(samples_dir / "sample_rfq.json", "w") as f:
        json.dump(json_rfq, f, indent=2)
    
    # Sample Email - Customer Complaint
    email_complaint = """From: angry.customer@email.com
To: support@company.com
Subject: URGENT: Defective Product - Order #12345
Date: Mon, 29 Jan 2024 14:30:00 +0000

Dear Support Team,

I am extremely disappointed with my recent purchase (Order #12345) placed on January 20th.

The product arrived damaged and is completely unusable. The packaging was torn and the device has visible cracks on the screen. This is unacceptable for a $800 purchase.

I need immediate action on this:
1. Full refund or replacement
2. Prepaid return shipping label
3. Explanation of how this happened

This has caused significant inconvenience as I needed this for an important presentation tomorrow. I expect a response within 24 hours or I will escalate this to consumer protection agencies.

Customer Details:
- Name: Robert Martinez
- Order: #12345
- Product: Premium Tablet Pro
- Purchase Date: 2024-01-20
- Amount: $799.99

I have been a loyal customer for 3 years but this experience is making me reconsider.

Regards,
Robert Martinez
robert.martinez@email.com
Phone: (555) 987-6543"""
    
    with open(samples_dir / "complaint_email.txt", "w") as f:
        f.write(email_complaint)
    
    # Sample Email - Business RFQ
    email_rfq = """From: procurement@techstartup.com
To: sales@vendors.com
Subject: RFQ for Cloud Infrastructure Services
Date: Tue, 30 Jan 2024 09:15:00 +0000

Hello Sales Team,

TechStartup Inc. is looking for a cloud infrastructure partner for our upcoming product launch.

Requirements:
- Cloud hosting for 100,000+ monthly active users
- 99.9% uptime SLA guarantee
- Auto-scaling capabilities
- Global CDN coverage
- Database management (PostgreSQL)
- Real-time analytics dashboard
- 24/7 technical support

Timeline:
- Proposal deadline: February 15, 2024
- Decision by: February 22, 2024
- Go-live date: March 15, 2024

Budget: $10,000 - $25,000 per month

Please include:
- Detailed technical specifications
- Pricing breakdown
- Case studies from similar clients
- Migration assistance plan
- Security compliance certificates

Contact for questions:
Lisa Chen, CTO
lisa.chen@techstartup.com
Direct: (555) 123-4567

Best regards,
Lisa Chen
Chief Technology Officer
TechStartup Inc."""
    
    with open(samples_dir / "rfq_email.txt", "w") as f:
        f.write(email_rfq)
    
    # Sample regulation text
    regulation_text = """REGULATION DOCUMENT

TITLE: Data Privacy and Security Compliance Guidelines
DOCUMENT ID: REG-2024-DPS-001
EFFECTIVE DATE: March 1, 2024
DEPARTMENT: Information Security

SECTION 1: PURPOSE AND SCOPE

This regulation establishes mandatory data privacy and security requirements for all business operations involving personal data collection, processing, and storage.

SECTION 2: DEFINITIONS

2.1 Personal Data: Any information relating to an identified or identifiable natural person
2.2 Data Controller: The entity that determines the purposes and means of processing personal data
2.3 Data Processor: The entity that processes personal data on behalf of the controller

SECTION 3: COMPLIANCE REQUIREMENTS

3.1 Data Collection
- Explicit consent must be obtained before collecting personal data
- Purpose limitation: data collected only for specified, explicit purposes
- Data minimization: collect only necessary data

3.2 Data Security
- Encryption required for all personal data in transit and at rest
- Regular security assessments mandatory
- Incident response plan must be maintained

3.3 Data Retention
- Personal data retained only as long as necessary
- Automatic deletion processes must be implemented
- Data retention schedules must be documented

SECTION 4: PENALTIES

Non-compliance may result in:
- Fines up to $100,000 per violation
- Suspension of data processing activities
- Mandatory compliance audits

SECTION 5: IMPLEMENTATION

Compliance deadline: June 1, 2024
All departments must submit compliance reports by May 15, 2024

This regulation supersedes all previous data privacy guidelines."""
    
    with open(samples_dir / "regulation_document.txt", "w") as f:
        f.write(regulation_text)
    
    print(f"Sample files created in {samples_dir}/")
    return samples_dir

def interactive_demo():
    """Run interactive demo"""
    
    print("=== Multi-Agent AI System Demo ===")
    print("This demo showcases document classification and processing")
    print()
    
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("⚠️  OPENROUTER_API_KEY environment variable not set!")
        api_key = input("Please enter your OpenRouter API key: ").strip()
        if not api_key:
            print("❌ No API key provided. Exiting.")
            return
    
    # Initialize system
    print("🚀 Initializing Multi-Agent System...")
    system = MultiAgentSystem(api_key)
    print("✅ System initialized successfully!")
    print()
    
    # Create sample files
    print("📁 Creating sample input files...")
    samples_dir = create_sample_files()
    print()
    
    # Demo scenarios
    scenarios = [
        {
            "name": "JSON Invoice Processing",
            "file": samples_dir / "sample_invoice.json",
            "description": "Process a structured invoice with item details and tax calculations"
        },
        {
            "name": "JSON RFQ Processing", 
            "file": samples_dir / "sample_rfq.json",
            "description": "Process a request for quote with technical specifications"
        },
        {
            "name": "Email Complaint Analysis",
            "file": samples_dir / "complaint_email.txt",
            "description": "Analyze customer complaint for sentiment and urgency"
        },
        {
            "name": "Email RFQ Processing",
            "file": samples_dir / "rfq_email.txt", 
            "description": "Extract business requirements from email communication"
        },
        {
            "name": "Regulation Document Analysis",
            "file": samples_dir / "regulation_document.txt",
            "description": "Process legal compliance document"
        }
    ]
    
    while True:
        print("\n" + "="*60)
        print("DEMO SCENARIOS:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. {scenario['name']}")
            print(f"   {scenario['description']}")
        print("6. Process custom file")
        print("7. View processing history")
        print("8. View thread context")
        print("0. Exit")
        print("="*60)
        
        choice = input("\nSelect option (0-8): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice in ["1", "2", "3", "4", "5"]:
            scenario = scenarios[int(choice) - 1]
            print(f"\n🔄 Processing: {scenario['name']}")
            print(f"📄 File: {scenario['file']}")
            print(f"📝 Description: {scenario['description']}")
            print()
            
            # Process the file
            result = system.process_file(str(scenario['file']))
            display_result(result)
            
        elif choice == "6":
            file_path = input("\nEnter file path: ").strip()
            if os.path.exists(file_path):
                result = system.process_file(file_path)
                display_result(result)
            else:
                print("❌ File not found!")
                
        elif choice == "7":
            print("\n📊 Processing History:")
            history = system.get_processing_history()
            if not history:
                print("No processing history found.")
            else:
                for entry in history[:10]:  # Show last 10
                    status_icon = "✅" if entry['status'] == 'success' else "❌"
                    print(f"{status_icon} {entry['timestamp'][:19]} | {entry['agent_type']} | {entry['source_type']}/{entry['intent']}")
                    
        elif choice == "8":
            thread_id = input("\nEnter thread ID: ").strip()
            if thread_id:
                context = system.get_context(thread_id)
                if context:
                    print(f"\n🧵 Context for thread '{thread_id}':")
                    print(f"Sender: {context.get('sender', 'N/A')}")
                    print(f"Topic: {context.get('topic', 'N/A')}")
                    print(f"Created: {context.get('created_at', 'N/A')}")
                    print(f"Updated: {context.get('updated_at', 'N/A')}")
                    print(f"Fields: {context.get('last_extracted_fields', {})}")
                else:
                    print("❌ Thread not found!")
        else:
            print("❌ Invalid option!")

def display_result(result):
    """Display processing result in a formatted way"""
    
    print("\n" + "="*50)
    print("PROCESSING RESULT")
    print("="*50)
    
    # Status
    status_icon = "✅" if result.success else "❌"
    print(f"Status: {status_icon} {'SUCCESS' if result.success else 'FAILED'}")
    
    # Basic info
    print(f"Agent: {result.agent_type}")
    print(f"Thread ID: {result.thread_id}")
    print(f"Timestamp: {result.timestamp}")
    
    # Classification
    print(f"\nClassification:")
    print(f"  Format: {result.classification.get('format', 'unknown')}")
    print(f"  Intent: {result.classification.get('intent', 'unknown')}")
    print(f"  Confidence: {result.classification.get('confidence', 'unknown')}")
    
    if result.success:
        print(f"\n📊 Extracted Data:")
        
        # Display relevant data based on agent type
        if result.agent_type == "json_agent":
            display_json_result(result.data)
        elif result.agent_type == "email_agent":
            display_email_result(result.data) 
        else:
            print(json.dumps(result.data, indent=2)[:500] + "...")
            
    else:
        print(f"\n❌ Errors:")
        for error in result.errors or []:
            print(f"  - {error}")
    
    print("="*50)

def display_json_result(data):
    """Display JSON agent results"""
    extracted = data.get('extracted_data', {})
    anomalies = data.get('anomalies', [])
    
    print("  Extracted Fields:")
    for key, value in extracted.items():
        print(f"    {key}: {value}")
    
    print(f"  Schema Compliance: {'✅ Yes' if data.get('schema_compliance') else '❌ No'}")
    
    if anomalies:
        print("  ⚠️  Anomalies Detected:")
        for anomaly in anomalies:
            print(f"    - {anomaly}")

def display_email_result(data):
    """Display email agent results"""
    extracted = data.get('extracted_info', {})
    urgency = data.get('urgency_level', 'unknown')
    crm_data = data.get('crm_formatted', {})
    
    print(f"  Sender: {extracted.get('sender', 'N/A')}")
    print(f"  Subject: {extracted.get('subject', 'N/A')}")
    print(f"  Sentiment: {extracted.get('sentiment', 'N/A')}")
    print(f"  Urgency: {urgency}")
    
    key_points = extracted.get('key_points', [])
    if key_points:
        print("  Key Points:")
        for point in key_points[:3]:  # Show first 3
            print(f"    - {point}")
    
    actions = extracted.get('action_items', [])
    if actions:
        print("  Action Items:")
        for action in actions[:3]:  # Show first 3
            print(f"    - {action}")
    
    print(f"  CRM Status: {crm_data.get('status', 'N/A')}")
    print(f"  CRM Priority: {crm_data.get('priority', 'N/A')}")

if __name__ == "__main__":
    try:
        interactive_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")

        print("Please check your API key and internet connection.")
