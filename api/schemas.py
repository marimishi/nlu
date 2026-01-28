from pydantic import BaseModel
from typing import Dict, Any, Optional, List


class CommandRequest(BaseModel):
    message: str
    session_id: str = ""


class CommandResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: str = ""


class TokenResponse(BaseModel):
    success: bool
    tokens: List[Dict[str, str]]
    simple_tokens: List[Dict[str, str]]
    message: str
    word_count: int
    method: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    processor_ready: bool


class ErrorResponse(BaseModel):
    detail: str