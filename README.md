# SiloSense – Multi-Agent Enterprise AI System

SiloSense is a multi-agent orchestration system that answers cross-domain enterprise queries by combining HR policies, project data, and technical documentation.

## 🔥 Features
- Multi-agent system (HR, PM, Tech)
- LangGraph orchestration
- RAG with ChromaDB
- Semantic search (Sentence Transformers)
- Real-time streaming UI (React)
- Agent trace visualization
- Conversational memory

## 🧠 Architecture

User Query  
→ LangGraph Orchestrator  
→ Select Agents  
→ Parallel Execution  
→ Retrieve (ChromaDB)  
→ LLM Synthesis (Groq)  
→ Final Response  

## ⚙️ Tech Stack
- Backend: FastAPI, LangGraph
- Vector DB: ChromaDB
- Embeddings: Sentence Transformers
- LLM: Groq (Llama 3.1)
- Frontend: React + Vite

## 💬 Example Queries
- What is the PTO policy?
- What is the wellness reimbursement amount?
- How does API authentication work?
- What is the status of TASK-101?
- Will TASK-101 delay affect my PTO?

## 🖼️ Screenshots
(Add UI screenshots here)

## 🚀 How to Run
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload

cd frontend
npm install
npm run dev