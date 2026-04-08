from __future__ import annotations
import typing
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from env import LegalEnv
from models import Action
from analyzer import DocumentAnalyzer

app = FastAPI(
    title="Legal Document Risk Analyzer API",
    version="1.0.0",
    description="FastAPI wrapper around the LegalEnv OpenEnv-compatible contract risk analysis environment.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "online",
        "message": "Legal Document Risk Analyzer API is running.",
        "endpoints": {
            "reset": "/reset?task={easy|medium|hard}",
            "step": "/step",
            "state": "/state",
            "analyze": "/analyze",
            "analyze_document": "/analyze-document",
            "docs": "/docs"
        }
    }


environment = LegalEnv()
analyzer = DocumentAnalyzer()


@app.get("/reset")
def reset(task: str = Query(..., pattern="^(easy|medium|hard)$")) -> Dict[str, Any]:
    try:
        observation = environment.reset(task)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "task": task.lower(),
        "observation": observation.model_dump(),
    }


@app.post("/step")
def step(action: Action) -> Dict[str, Any]:
    try:
        observation, reward, done, info = environment.step(action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "observation": observation.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    }


from pydantic import BaseModel

class DocumentInput(BaseModel):
    document: str


@app.get("/state")
def state() -> Dict[str, Any]:
    return {
        "observation": environment.state().model_dump(),
    }


@app.post("/analyze")
async def analyze_full_text(input: DocumentInput):
    if not input.document.strip():
        raise HTTPException(status_code=400, detail="Document cannot be empty.")
    
    report = await analyzer.analyze_document(input.document)
    return report


@app.post("/analyze-document")
async def analyze_document_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported for now.")
    
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    
    report = await analyzer.analyze_document(text)
    report["filename"] = file.filename
    return report

