"""API маршруты для сервиса классификации команд."""
from typing import Any
from fastapi import APIRouter, HTTPException, Request

from ..config.model_config import ModelConfig   # pylint: disable=relative-beyond-top-level
from .schemas import (CommandRequest, CommandResponse, HealthResponse,
                      TokenResponse)

router = APIRouter()


def get_nlu_service(request: Request):
    """
    Получить NLU сервис из состояния приложения.

    Args:
        request: HTTP запрос с доступом к состоянию приложения

    Returns:
        NLU сервис для обработки естественного языка

    Raises:
        HTTPException: Если NLU сервис недоступен (503)
    """
    nlu_service = getattr(request.app.state, 'nlu_service', None)
    if not nlu_service:
        raise HTTPException(
            status_code=503, detail="NLU service not available")
    return nlu_service


def get_processor(request: Request):
    """
    Получить процессор команд из состояния приложения.

    Args:
        request: HTTP запрос с доступом к состоянию приложения

    Returns:
        Процессор команд для обработки извлеченных команд

    Raises:
        HTTPException: Если процессор недоступен (503)
    """
    processor = getattr(request.app.state, 'processor', None)
    if not processor:
        raise HTTPException(
            status_code=503, detail="Command processor not available")
    return processor


@router.get("/", response_model=dict[str, Any])
async def root() -> dict[str, Any]:
    """
    Главная страница API.

    Returns:
        Словарь с информацией о сервисе, версией и доступными маршрутами
    """
    return {
        "service": ModelConfig.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "health/ready": "/health/ready",
            "health/live": "/health/live",
            "process": "/api/v1/process",
            "process_old": "/api/v1/process_old",
            "tokens": "/api/v1/tokens"
        }
    }


@router.get("/health", response_model=HealthResponse)
@router.get("/health/ready", response_model=HealthResponse)
@router.get("/health/live", response_model=HealthResponse)
async def health_check(request: Request):
    """
    Проверка здоровья сервиса.

    Доступен на трех маршрутах: /health, /health/ready, /health/live

    Args:
        request: HTTP запрос

    Returns:
        HealthResponse с статусом сервиса, загруженностью модели и
        готовностью обработчика
    """
    nlu_service = get_nlu_service(request)

    return HealthResponse(
        status="healthy",
        model_loaded=nlu_service.ner_service.is_model_loaded(),
        processor_ready=request.app.state.processor is not None
    )


@router.post("/api/v1/process_old", response_model=CommandResponse)
async def process_command_old(
    request: Request,
    command_request: CommandRequest
):
    """
    Обработать текстовую команду и классифицировать её.

    Извлекает сущности из входящего текста, определяет команду 
    и возвращает структурированный результат с параметрами.

    Args:
        request: HTTP запрос
        command_request: Запрос с текстом команды для обработки

    Returns:
        CommandResponse с результатом обработки (команда, параметры, модуль)

    Raises:
        HTTPException: Если сервис недоступен (503)
    """
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
    except (ValueError, KeyError, AttributeError, TypeError) as e:
        return CommandResponse(
            success=False,
            data={},
            error=f"Processing error: {str(e)}"
        )
    except Exception as e:  # pylint: disable=broad-except
        # Log unexpected errors for debugging
        print(
            f"Unexpected error in process_command: {type(e).__name__}: {str(e)}")
        return CommandResponse(
            success=False,
            data={},
            error="Internal server error"
        )


@router.post("/api/v1/process", response_model=CommandResponse)
async def process_command(
    request: Request,
    command_request: CommandRequest
):
    """
    Обработать текстовую команду и классифицировать её.
    
    Извлекает сущности из входящего текста, определяет команду
    и возвращает структурированный результат с параметрами и отладочной информацией.

    Args:
        request: HTTP запрос
        command_request: Запрос с текстом команды для обработки

    Returns:
        CommandResponse с результатом обработки (команда, параметры, модуль, отладка)
        
    Raises:
        HTTPException: Если сервис недоступен (503)
    """
    try:
        nlu_service = get_nlu_service(request)
        processor = get_processor(request)

        result = nlu_service.process_text(command_request.message, processor)

        if "debug_info" in result:
            result["debug_info"]["original_text"] = command_request.message

        return CommandResponse(
            success=True,
            data={
                "parameters": result.get("parameters", {}),
                "command": result.get("command", "UNKNOWN"),
                "moduleName": result.get("moduleName", ""),
                "moduleId": result.get("moduleId", ""),
                "moduleTitle": result.get("moduleTitle", ""),
                "debug_info": result.get("debug_info", {})
            },
            error=""
        )

    except HTTPException:
        raise
    except (ValueError, KeyError, AttributeError, TypeError) as e:
        return CommandResponse(
            success=False,
            data={},
            error=f"Processing error: {str(e)}"
        )
    except Exception as e:  # pylint: disable=broad-except
        print(f"Unexpected error in process_command: {type(e).__name__}: {str(e)}")
        return CommandResponse(
            success=False,
            data={},
            error="Internal server error"
        )

@router.post("/api/v1/tokens", response_model=TokenResponse)
async def get_tokens(
    request: Request,
    command_request: CommandRequest
):
    """
    Извлечь и проанализировать токены из текста команды.

    Выполняет токенизацию входящего текста и выделение именованных сущностей (NER).
    Возвращает информацию о найденных токенах и сущностях.

    Args:
        request: HTTP запрос
        command_request: Запрос с текстом для анализа

    Returns:
        TokenResponse с информацией о токенах, сущностях и методе анализа

    Raises:
        HTTPException: Если сервис недоступен (503)
    """
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
    except (ValueError, KeyError, AttributeError, TypeError) as e:
        return TokenResponse(
            success=False,
            tokens=[],
            simple_tokens=[],
            message=command_request.message,
            word_count=0,
            method="error",
            error=f"Processing error: {str(e)}"
        )
    except Exception as e:  # pylint: disable=broad-except
        # Log unexpected errors for debugging
        print(f"Unexpected error in get_tokens: {type(e).__name__}: {str(e)}")
        return TokenResponse(
            success=False,
            tokens=[],
            simple_tokens=[],
            message=command_request.message,
            word_count=0,
            method="error",
            error="Internal server error"
        )
