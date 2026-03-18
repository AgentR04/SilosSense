from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph.workflow import build_graph

app = FastAPI(title="SiloSense API")

graph = build_graph()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    text: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

@app.get("/")
def home():
    return {"message": "SiloSense backend is running"}

@app.post("/chat")
def chat(request: ChatRequest):
    result = graph.invoke({
        "user_query": request.message,
        "chat_history": [{"role": msg.role, "text": msg.text} for msg in request.history]
    })

    return {
        "agent": "LangGraph Orchestrator",
        "reply": result["final_answer"],
        "source": ", ".join(result.get("sources", [])),
        "trace": result.get("trace", {})
    }