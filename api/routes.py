from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

from api.schemas import (
    CommandRequest, 
    CommandResponse, 
    TokenResponse,
    HealthResponse
)


router = APIRouter()


def get_nlu_service(request: Request):
    nlu_service = getattr(request.app.state, 'nlu_service', None)
    if not nlu_service:
        raise HTTPException(status_code=503, detail="NLU service not available")
    return nlu_service


def get_processor(request: Request):
    processor = getattr(request.app.state, 'processor', None)
    if not processor:
        raise HTTPException(status_code=503, detail="Command processor not available")
    return processor


@router.get("/", response_model=Dict[str, Any])
async def root():
    from config.model_config import ModelConfig
    
    return {
        "service": ModelConfig.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "process": "/api/v1/process",
            "tokens": "/api/v1/tokens"
        }
    }


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    nlu_service = get_nlu_service(request)
    
    return HealthResponse(
        status="healthy",
        model_loaded=nlu_service.ner_service.is_model_loaded(),
        processor_ready=request.app.state.processor is not None
    )


@router.post("/process", response_model=CommandResponse)
async def process_command(
    request: Request,
    command_request: CommandRequest
):
    try:
        nlu_service = get_nlu_service(request)
        processor = get_processor(request)
        
        result = nlu_service.process_text(command_request.message, processor)
        
        return CommandResponse(
            success=True,
            data={
                "parameters": result.get("parameters", {}),
                "command": result.get("command", "UNKNOWN"),
                "moduleName": result.get("moduleName", ""),
                "moduleId": result.get("moduleId", ""),
                "moduleTitle": result.get("moduleTitle", "")
            },
            error=""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return CommandResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.post("/tokens", response_model=TokenResponse)
async def get_tokens(
    request: Request,
    command_request: CommandRequest
):
    try:
        nlu_service = get_nlu_service(request)
        
        token_info = nlu_service.extract_tokens(command_request.message)
        
        return TokenResponse(
            success=True,
            tokens=token_info["ner_tokens"],
            simple_tokens=token_info["simple_tokens"],
            message=command_request.message,
            word_count=len(command_request.message.split()),
            method=token_info["method"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return TokenResponse(
            success=False,
            tokens=[],
            simple_tokens=[],
            message=command_request.message,
            word_count=0,
            method="error",
            error=str(e)
        )