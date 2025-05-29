🧠 Multi-Agent AI System
This project is a multi-agent AI system that classifies inputs (PDF, JSON, Email), determines the intent, and routes them to specialized agents. It includes a Streamlit interface for interaction, debugging, and demonstration.

🚀 Features
📂 Upload PDF, JSON, or Email files, or input raw text

🔍 Automatic format and intent classification

🤖 Routes data to appropriate agent (PDF, JSON, Email)

📈 Displays extracted information, analysis, and agent confidence

🕵️ History of results for comparison and review

📁 Folder Structure
arduino
Copy
Edit
.
├── agents/
│   ├── classifier.py
│   ├── email_agent.py
│   ├── json_agent.py
│   ├── pdf_agent.py
├── core/
│   └── multi_agent_system.py
├── streamlit_app.py         <- Streamlit UI entry point
├── requirements.txt
└── README.md
🧩 Requirements
Create and activate a virtual environment (optional but recommended):

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Contents of requirements.txt (if not already created):

txt
Copy
Edit
streamlit
matplotlib
Add any other libraries you use (e.g., PyMuPDF, langchain, mistralai, etc.)

▶️ Run the Streamlit App
bash
Copy
Edit
streamlit run streamlit_app.py
Then open the link that appears (usually http://localhost:8501) in your browser.

📷 Demo Screenshot
(Optional: Add a screenshot of the UI here)

📌 Example Inputs
Upload:

A .pdf file with textual content

A .json file (with business data)

A .txt file representing a raw email

Or paste raw email/JSON/text into the input box.

📦 Output Details
For each input, the app shows:

Detected Format, Intent, and Agent

Extracted metadata (emails, keys, fields, etc.)

Agent confidence

Structured or summarized results

Raw content (collapsible)

🛠️ Development Notes
MultiAgentSystem routes input after classification

Add your own logic inside each agent (email_agent.py, etc.)

Classifier currently uses a rule-based or ML model approach (customizable)

📄 License
MIT License (or your preferred license)
