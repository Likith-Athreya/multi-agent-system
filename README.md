# 🤖 Multi-Agent AI System: Intelligent Document Classifier & Router

This project is a Multi-Agent AI System that intelligently classifies uploaded documents (PDF, JSON, or Email), detects their intent using an LLM, and routes them to specialized agents (like JSON Agent or Email Agent) for processing. It also demonstrates shared memory design and conversational feedback.

🌐 **Live Demo**: [Launch the App](https://titanic-chatbo-9xjkgqmj9kekkbgxbysqjf.streamlit.app/)

---

## 📽️ Demo Video

[Click here to watch the demo](https://drive.google.com/your-demo-link)

---

## 🧠 System Overview

- **Classifier Agent**: Identifies file format and intent using LLM (Mistral via OpenRouter).
- **JSON Agent**: Extracts structured insights from `.json` files.
- **Email Agent**: Parses `.eml` emails and replies based on content.
- **Shared Memory**: Lightweight memory (JSON file/Redis) for agent coordination.
- **Streamlit UI**: Upload files and view agent results interactively.

---

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend**: Python
- **LLM API**: Mistral 7B via [OpenRouter](https://openrouter.ai/)
- **Agents**: Custom Python modules for classification, parsing, routing

---

## 🚀 Getting Started (Local)

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/multi-agent-system.git
cd multi-agent-system
2. Set Up Python Environment
bash
Copy
Edit
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
3. Add API Keys
Create a .env file:

bash
Copy
Edit
cp .env.example .env
Add your OpenRouter API key:

ini
Copy
Edit
OPENROUTER_API_KEY=your-api-key-here
⚙️ Run the App Locally
bash
Copy
Edit
streamlit run streamlit_app.py
🧪 Sample Usage
Upload any of these file types:

data/sample.json

data/email.eml

data/invoice.pdf

The app will:

Classify the file type and intent

Route it to the appropriate agent

Display results in a readable format

📦 Dependencies
makefile
Copy
Edit
requests==2.31.0
PyPDF2==3.0.1
streamlit>=1.25.0
python-dotenv
rich
Install via:

bash
Copy
Edit
pip install -r requirements.txt
📂 Project Structure
pgsql
Copy
Edit
multi-agent-system/
├── agents/
│   ├── classifier_agent.py
│   ├── json_agent.py
│   └── email_agent.py
├── shared_memory/
│   └── memory.py
├── data/
│   ├── sample.json
│   └── email.eml
├── main.py
├── streamlit_app.py
├── requirements.txt
├── .env.example
└── README.md
✍️ Author's Notes
LLM prompt tuning is critical for reliable format/intent classification.

Designed to be extensible: add more file-type agents easily.

Shared memory allows parallel agent execution and centralized data tracking.

📜 License
This project is licensed under the MIT License.
