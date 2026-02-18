import json
import os
from typing import Dict, Any
from pathlib import Path

from config.model_config import ModelConfig


class KnowledgeBase:
    def __init__(self):
        self.registry = {}
        self.target_synonyms = {}
        self.load_registry()
    
    def load_registry(self) -> None:
        registry_path = ModelConfig.REGISTRY_PATH
        
        if os.path.exists(registry_path):
            with open(registry_path, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)
        else:
            self.registry = self.get_default_registry()
        
        self.target_synonyms = self.extract_synonyms_from_registry()
    
    def get_default_registry(self) -> Dict[str, Any]:
        registry_path = Path("../data/registry.json")

        if not registry_path.exists():
            raise FileNotFoundError(f"Registry file not found: {registry_path}")

        with registry_path.open(encoding="utf-8") as f:
            return json.load(f)
    
    def extract_synonyms_from_registry(self) -> Dict[str, list]:
        synonyms = {
        "Ois.Modules.chessy.ChessyModule": ["шахматка", "шахматку"],
        "10054": ["редактор слушателей очередей"],
        "10037": ["аудит-данные", "аудит - данные", "аудит данные", "аудит данных"],
        "10038": ["аудит - лог приложения", "аудит лог приложения", "аудит логи приложения", "аудит лог", "аудит логи"],
        "10039": ["аудит - лог расчетов", "аудит лог расчетов", "аудит логи расчетов", "лог расчетов аудита", "логи расчетов аудита"],
        "10040": ["аудит структура вд", "аудит структуру вд"],
        "10041": ["аудит - события", "аудит события", "аудит событий"],
        "10031": ["информация о системе", "информацию о системе"],
        "10042": ["брокеры очередей"],
        "10043": ["потоковая загрузка", "потоковую загрузку"],
        "10044": ["репликация данных", "репликацию данных"],
        "10045": ["параметры контекста"],
        "10046": ["службы"],
        "10048": ["экспорт"],
        "10050": ["редактор форматов отчетов"],
        "10052": ["редактор меню"],
        "10056": ["редактор процессов"],
        "10058": ["редактор типов данных"],
        "10060": ["редактор вд"],
        "10062": ["настройка уведомлений", "настройки уведомлений"],
        "10064": ["формы"],
        "forms_input_engine": ["движок форм", "формы ввода", "движок форм ввода"],
        "reporting_engine": ["движок отчетности", "отчетность"],
        "wells_registry": ["реестр скважин", "реестр объектов", "реестр"],
        "nsi": ["нси", "нс и"],
        "fund_maintenance": ["ведение фонда", "фонд"],
        "run_or_stop": ["запуски-остановки", "запуски", "остановки"],
        "mode_output": ["вывод на режим", "режим"],
        "volume_balance": ["баланс объемов", "баланс"],
        "standalone_report": ["отчет", "отчёты", "сводка", "доклад", "аудит"],
        "well_construction": [
            "конструкция",
            "конструкцию",
            "конструкция скважины",
            "конструкцию скважины",
            "данные по конструкции",
            "схема конструкции",
            "схему конструкции"
        ],
        "annual_planning": ["годовое планирование", "планирование"],
        "wellhead_survey": ["обследование устьев", "устья скважин"],
        "technological_mode": ["технологический режим", "тех режим"],
        "measurements_verification": ["верификация замеров", "верификация"],
        }
        return synonyms
    
    def get_module_info(self, module_id: str) -> Dict[str, Any]:
        return self.registry.get(module_id, {})
    
    def find_module_by_synonym(self, target_text: str) -> str:
        target_text = target_text.lower()
        
        for module_id, synonyms in self.target_synonyms.items():
            for synonym in synonyms:
                synonym_lower = synonym.lower()
                if synonym_lower == target_text:
                    return module_id
                elif synonym_lower in target_text:
                    return module_id
                elif target_text in synonym_lower:
                    return module_id
        
        return None
    
    def find_module_in_text(self, text: str) -> str:
        text = text.lower()
        
        for module_id, synonyms in self.target_synonyms.items():
            for synonym in synonyms:
                if synonym.lower() in text:
                    return module_id
        
        return None