"""Модуль схем данных для API классификатора команд.

Этот модуль содержит Pydantic модели для валидации и сериализации
данных, передаваемых через API классификатора команд.
"""
from typing import Any
from pydantic import BaseModel


class CommandRequest(BaseModel):
    """Схема запроса для обработки команды.
    
    Attributes:
        message (str): Текст сообщения команды для обработки.
        session_id (str): Идентификатор сессии пользователя. По умолчанию пустая строка.
    """
    message: str
    session_id: str = ""


class CommandResponse(BaseModel):
    """Схема ответа для обработки команды.
    
    Attributes:
        success (bool): Флаг успешности обработки команды.
        data (dict[str, Any]): Данные результата обработки команды.
        error (str): Сообщение об ошибке, если возникла. По умолчанию пустая строка.
    """
    success: bool
    data: dict[str, Any]
    error: str = ""


class TokenResponse(BaseModel):
    """Схема ответа для токенизации текста.
    
    Attributes:
        success (bool): Флаг успешности токенизации.
        tokens (list[dict[str, str]]): Список токенов с их типами.
        simple_tokens (list[dict[str, str]]): Упрощенный список токенов.
        message (str): Исходное сообщение.
        word_count (int): Количество слов в сообщении.
        method (str): Метод токенизации.
        error (str): Сообщение об ошибке, если возникла. По умолчанию пустая строка.
    """
    success: bool
    tokens: list[dict[str, str]]
    simple_tokens: list[dict[str, str]]
    message: str
    word_count: int
    method: str
    error: str = ""


class HealthResponse(BaseModel):
    """Схема ответа для проверки состояния сервиса.
    
    Attributes:
        status (str): Статус сервиса.
        model_loaded (bool): Флаг загрузки модели.
        processor_ready (bool): Флаг готовности процессора.
    """
    status: str
    model_loaded: bool
    processor_ready: bool


class ErrorResponse(BaseModel):
    """Схема ответа для ошибок.
    
    Attributes:
        detail (str): Подробное описание ошибки.
    """
    detail: str