from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

from models.ner_model import NERModel
from models.processor import CommandProcessor
from config.config import config

class CommandRequest(BaseModel):
    message: str
    session_id: str = ""

class CommandResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: str = ""

app = FastAPI(
    title=config.APP_NAME,
    description=config.APP_DESCRIPTION,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ner_model = None
processor = None

@app.on_event("startup")
async def startup_event():
    global ner_model, processor
    try:
        ner_model = NERModel()
        processor = CommandProcessor()
        print("NLU Service started successfully")
    except Exception as e:
        print(f"Error loading NER model: {e}")
        processor = CommandProcessor()

@app.get("/")
async def root():
    return {
        "service": config.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "process": "/api/v1/process",
            "tokens": "/api/v1/tokens"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": ner_model is not None,
        "processor_ready": processor is not None
    }

@app.post("/api/v1/process", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    try:
        if not processor:
            raise HTTPException(status_code=503, detail="Service not ready")
        
        if ner_model:
            try:
                ner_results = ner_model.predict(request.message)
                result = processor.process_command(request.message, ner_results)
            except Exception:
                result = processor.rule_based_processor(request.message)
        else:
            result = processor.rule_based_processor(request.message)
        
        return CommandResponse(
            success=True,
            data={
                "connectionId": result.get("connectionId", ""),
                "parameters": result.get("parameters", {}),
                "command": result.get("command", "UNKNOWN")
            },
            error=""
        )
        
    except Exception as e:
        return CommandResponse(
            success=False,
            data={},
            error=str(e)
        )

@app.post("/api/v1/tokens")
async def get_tokens(request: CommandRequest):
    try:
        if ner_model:
            ner_results = ner_model.predict(request.message)
            method = "ner_model"
        else:
            ner_results = [
                {"token": word, "tag": "O"} 
                for word in request.message.split()
            ]
            method = "simple_split"
        
        simple_tokens = [
            {"token": word, "tag": "O"} 
            for word in request.message.split()
        ]
        
        return {
            "success": True,
            "tokens": ner_results,
            "simple_tokens": simple_tokens,
            "message": request.message,
            "word_count": len(request.message.split()),
            "method": method
        }
        
    except Exception as e:
        return {
            "success": False,
            "tokens": [],
            "error": str(e),
            "method": "error"
        }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )