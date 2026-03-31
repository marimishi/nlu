"""Конфигурационный модуль для модели NLU сервиса.

Этот модуль содержит настройки для модели NLU сервиса, включая:
- Параметры модели BERT
- Настройки сервера (хост, порт, режим отладки)
- Конфигурацию API
- Пути к данным
"""
import os
from dotenv import load_dotenv

load_dotenv()


class ModelConfig:
    """Конфигурационный класс для модели NLU сервиса.

    Содержит настройки для модели NLU сервиса, включая:
    - Параметры модели BERT
    - Настройки сервера (хост, порт, режим отладки)
    - Конфигурацию API
    - Пути к данным
    """

    MODEL_NAME = "DeepPavlov/rubert-base-cased"
    MODEL_PATH = "app/data/trained_model"

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8080"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    API_VERSION = "v1"
    APP_NAME = "NLU Service"
    APP_DESCRIPTION = "Natural Language Understanding Service for Oil & Gas Commands"

    # Пути к данным
    REGISTRY_PATH = "app/data/registry.json"

    @classmethod
    def get_model_info(cls) -> dict[str, str]:
        """Возвращает информацию о конфигурации модели.

        Returns:
            dict[str, str]: Словарь с информацией о модели
        """
        return {
            "model_name": cls.MODEL_NAME,
            "model_path": cls.MODEL_PATH,
            "api_version": cls.API_VERSION,
            "app_name": cls.APP_NAME,
            "app_description": cls.APP_DESCRIPTION
        }

    @classmethod
    def get_server_config(cls) -> dict[str, str | int | bool]:
        """Возвращает конфигурацию сервера.

        Returns:
            dict[str, str | int | bool]: Словарь с настройками сервера
        """
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "debug": cls.DEBUG
        }
