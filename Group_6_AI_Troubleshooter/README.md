# 🤖 MATFix AI — MATLAB Troubleshooting Assistant

**Team 6 | Deep Learning Hackathon | Sponsored by HCLTech**  
**An intelligent agent-based system to diagnose and resolve MATLAB-related issues.**

MATFix AI is an interactive, multi-agent system that leverages advanced AI models and architectures to troubleshoot MATLAB errors. Designed with scalability, modularity, and explainability in mind, this system intelligently interprets user queries, extracts insights from MATLAB documentation, and provides crystal-clear guidance to fix issues.

📽️ [Understand Our Approach (Slides)](https://www.canva.com/design/DAGmbL8Vyeo/pvdwE1Hyc-AQbAsfsh9XKw/edit?utm_content=DAGmbL8Vyeo&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)

---

## 🚀 Features

- 🧠 **Agentic Architecture** using CRAG + SRAG (Retrieval + Generation)
- 📚 **MATLAB-aware RAG System** using FAISS vector DB
- 🌐 **FastAPI + Next.js based frontend-backend integration**
- 🌐 **MCP Server for Claude Desktop**
- 📦 **VSCode-compatible extension**
- 📊 **Streamlit interface for fast prototyping**
- 🧪 **MATLAB error testing scripts**
- ☁️ Hosted via **NGROK** for global access

---

## 📁 Repository Structure

```

DL-Hackathon/
│
├── MCP/
│   └── matlab\_troubleshooter/
│       ├── pyproject.toml  # Use `uv` to install and run
│
├── vscode\_extension/
│   └── matlab\_troubleshooter/
│       └── \[VSCode Extension Files]
│
├── frontend/
│   └── \[Next.js Frontend App]
│
├── script/
│   ├── agent\_main.py
│   └── combined\_rag\_final.py
│
├── agents/
│   ├── base\_agent.py
│   ├── evaluation\_agent.py
│   ├── generation\_agent.py
│   ├── image\_analysis\_agent.py
│   ├── models.py
│   ├── orchestrator.py
│   ├── retrieval\_agent.py
│   └── web\_search\_agent.py
│
├── FAISS\_index/
│   └── \[Vector DB files]
│
├── main.py                # FastAPI backend
├── main-streamlit.py      # Streamlit UI version
├── requirements.txt
├── .env.example
└── README.md

````

---

## ⚙️ Installation & Setup Guide

### 1️⃣ Clone the Repo & Create Virtual Environment

```bash
git clone https://github.com/ABHIJEETJHA0102/DL-Hackathon.git
cd DL-Hackthon
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
````

### 2️⃣ Setup `.env`

Rename the `.env.example` to `.env` and fill in your required API keys:

```bash
cp .env.example .env
# then edit `.env` to include OpenAI / NGROK keys etc.
```

---

## 📦 Components

### 🔹 `MCP/matlab_troubleshooter`

* Built for the **Model Context Protocol (MCP)**.
* **Setup**:

  ```bash
  pip install uv
  uv run  # Automatically installs dependencies via pyproject.toml
  ```
* Add `matlab_troubleshooter` to your Claude Desktop config.

---

### 🔹 `vscode_extension/matlab_troubleshooter`

* VSCode Extension.
* **Run**: Press `Ctrl + Shift + D` ➝ Click ▶️ "Run Extension".

---

### 🔹 `frontend` (Next.js Frontend)

* Requires Node.js (v18+ recommended)
* **Setup**:

  ```bash
  cd frontend
  npm install
  npm run dev
  ```
* Visit: [http://localhost:3000](http://localhost:3000)

> ⚠️ Make sure your `main.py` FastAPI server is running before starting frontend.

---

### 🔹 `script/`

Contains test scripts:

* `agent_main.py`: Runs agent pipeline
* `combined_rag_final.py`: Combines CRAG + SRAG logic

---

### 🔹 `agents/` Directory

Houses all core agents of MATFix AI:

| Agent File                | Description                                                        |
| ------------------------- | ------------------------------------------------------------------ |
| `base_agent.py`           | Abstract base class defining standard interface for all agents     |
| `evaluation_agent.py`     | Evaluates responses for correctness, coherence, and accuracy       |
| `generation_agent.py`     | Handles final answer generation using GPT models                   |
| `image_analysis_agent.py` | Analyzes visual errors or screenshots from MATLAB console          |
| `models.py`               | Model and utility definitions (e.g., response schema, agent state) |
| `orchestrator.py`         | Manages multi-agent coordination and state passing                 |
| `retrieval_agent.py`      | Fetches relevant chunks from FAISS-indexed MATLAB documentation    |
| `web_search_agent.py`     | Queries online sources like MathWorks forums, StackOverflow, etc.  |

> ✅ We've implemented **CRAG (Contextual RAG)** and **SRAG (Sequential RAG)** architectures.

---

### 🔹 `main.py` (FastAPI Backend)

* Backend for Next.js UI
* **Run with Uvicorn**:

  ```bash
  uvicorn main:app --reload
  ```

---

### 🔹 `main-streamlit.py` (Streamlit App)

* UI for demo and testing
* **Run**:

  ```bash
  streamlit run main-streamlit.py
  ```

---

### 🔹 `FAISS_index/`

Contains vector store generated via `sentence-transformers/all-mpnet-base` for fast semantic search over MATLAB docs.

---

## 🌐 Hosting

We use [NGROK](https://ngrok.com/) to expose local FastAPI backend globally.

```bash
ngrok http 8000
```

---

## 🧰 Tech Stack

| Category          | Tools Used                                                 |
| ----------------- | ---------------------------------------------------------- |
| LLM Framework     | ![LangChain](https://img.shields.io/badge/-LangChain-blue) |
| Frontend          | Next.js, Streamlit                                         |
| Backend           | FastAPI                                                    |
| Vector DB         | FAISS + Sentence Transformers                              |
| Extensions        | VSCode Extensions                                          |
| Deployment        | NGROK                                                      |
| Protocols         | Model Context Protocol (MCP)                               |
| Programming Lang. | Python                                                     |
| Logging & History | Zep                                                        |

---

## 🙏 Acknowledgments

A big thanks to:

* **Dr. Aditya Nigam**
* **Dr. Arnav Bhavsar**
* **Our Mentor: Kajal Mam**

for their invaluable guidance and this incredible opportunity.

---

## 👨‍👩‍👧‍👦 Team Members — Team 6

| Name     | Roll Number |
| -------- | ----------- |
| Saurabh Kumar Sonkar | B22175    |
| Abhijeet Kumar Jha | B22149    |
| Sameer Rawat | B22172    |
| Ch. Sunil Patra | B22294   |
| Tarun Srivastava | B22333    |
| Nani Panyu | B22054  |

---

## 📬 Contact

For queries or contributions, feel free to open an issue or submit a pull request.

---
