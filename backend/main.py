from dotenv import load_dotenv
load_dotenv()

from typing import List
from pathlib import Path
import shutil
import time

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph.workflow import build_graph
from scripts.ingest_hr import ingest_hr_docs
from scripts.ingest_tech import ingest_tech_docs
from services.analytics import get_analytics, record_query
from services.trace_visibility import filter_trace_by_role

app = FastAPI(title="SiloSense API")
print("SiloSense backend starting...")

graph = build_graph()

BASE_DATA_DIR = Path(__file__).resolve().parent / "data"
HR_DATA_DIR = BASE_DATA_DIR / "hr"
TECH_DATA_DIR = BASE_DATA_DIR / "tech"

SUPPORTED_HR_UPLOAD_EXTENSIONS = {".pdf"}
SUPPORTED_TECH_UPLOAD_EXTENSIONS = {".md", ".markdown", ".txt", ".doc"}

HR_DATA_DIR.mkdir(parents=True, exist_ok=True)
TECH_DATA_DIR.mkdir(parents=True, exist_ok=True)

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
    role: str = "employee"
    workspace: str = "all"

@app.get("/")
def home():
    return {"message": "SiloSense backend is running"}

@app.post("/chat")
def chat(request: ChatRequest):
    start = time.perf_counter()

    result = graph.invoke({
        "user_query": request.message,
        "chat_history": [{"role": msg.role, "text": msg.text} for msg in request.history],
        "role": request.role,
        "workspace": request.workspace,
    })

    response_time_ms = round((time.perf_counter() - start) * 1000, 2)
    raw_trace = result.get("trace", {})
    record_query(raw_trace, response_time_ms)
    visible_trace = filter_trace_by_role(raw_trace, request.role)

    return {
        "agent": "LangGraph Orchestrator",
        "reply": result["final_answer"],
        "source": ", ".join(result.get("sources", [])),
        "trace": visible_trace,
        "response_time_ms": response_time_ms,
    }


@app.post("/upload")
def upload_file(domain: str, file: UploadFile = File(...)):
    if domain not in ["hr", "tech"]:
        raise HTTPException(status_code=400, detail="Invalid domain")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_name = Path(file.filename).name
    file_extension = Path(file_name).suffix.lower()

    if domain == "hr" and file_extension not in SUPPORTED_HR_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="HR uploads support only .pdf files")

    if domain == "tech" and file_extension not in SUPPORTED_TECH_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tech uploads support .md, .markdown, .txt, .doc files")

    target_dir = HR_DATA_DIR if domain == "hr" else TECH_DATA_DIR
    file_path = target_dir / file_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": f"{file_name} uploaded successfully to {domain}",
        "filename": file_name,
        "domain": domain,
    }


@app.post("/reindex")
def reindex(domain: str):
    if domain == "hr":
        ingest_hr_docs()
        return {"message": "HR documents reindexed successfully"}

    if domain == "tech":
        ingest_tech_docs()
        return {"message": "Tech documents reindexed successfully"}

    raise HTTPException(status_code=400, detail="Invalid domain")


@app.get("/files")
def list_files(domain: str):
    if domain == "hr":
        files = [f.name for f in HR_DATA_DIR.glob("*") if f.is_file()]
    elif domain == "tech":
        files = [f.name for f in TECH_DATA_DIR.glob("*") if f.is_file()]
    else:
        raise HTTPException(status_code=400, detail="Invalid domain")

    return {
        "domain": domain,
        "files": sorted(files),
    }


@app.get("/analytics")
def analytics():
    return get_analytics()