"""
Модуль содержит класс NLUCommand для представления команды NLU (Natural Language Understanding).
"""

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NLUCommand:
    """
    Класс для представления команды NLU (Natural Language Understanding).
    
    Содержит информацию о команде, параметрах, модуле и отладочной информации.
    """
    connection_id: str = ""
    parameters: dict[str, Any] | None = None
    command: str = "UNKNOWN"
    module_name: str = ""
    module_id: str = ""
    module_title: str = ""
    debug_info: dict[str, Any] = field(default_factory=lambda: {
        "raw_tokens": [],
        "entities_found": [],
        "text_processed": "",
        "method": "",
        "timestamp": ""
    })

    def to_dict(self) -> dict[str, Any]:
        """
        Преобразует объект команды в словарь.
        
        Returns:
            dict[str, Any]: Словарь с данными команды.
        """
        result: dict[str, Any] = {
            "connectionId": self.connection_id,
            "command": self.command,
            "moduleName": self.module_name,
            "moduleId": self.module_id,
            "moduleTitle": self.module_title,
            "debug": self.debug_info
        }
        if self.parameters is not None:
            result["parameters"] = self.parameters
        return result

    @classmethod
    def create_from_analysis(cls, text: str, entities: dict[str, Any],
                             method: str = "ner") -> 'NLUCommand':
        """
        Создает объект команды на основе анализа текста.
        
        Args:
            text (str): Текст для анализа.
            entities (dict[str, Any]): Найденные сущности.
            method (str, optional): Метод анализа. По умолчанию "ner".
            
        Returns:
            NLUCommand: Объект команды.
        """
        command = cls()
        command.debug_info["text_processed"] = text
        command.debug_info["entities_found"] = entities
        command.debug_info["method"] = method
        command.debug_info["timestamp"] = datetime.now().isoformat()

        return command
