import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from .constants import TARGET_SYNONYMS, REGISTRY, INTENTS


class CommandProcessor:
    def __init__(self):
        self.registry = REGISTRY
    
    def find_module_by_target(self, target_text: str) -> Optional[str]:
        target_text = target_text.lower()
        
        for module_id, synonyms in TARGET_SYNONYMS.items():
            for synonym in synonyms:
                synonym_lower = synonym.lower()
                if synonym_lower == target_text:
                    return module_id
                elif synonym_lower in target_text:
                    return module_id
                elif target_text in synonym_lower:
                    return module_id
        
        return None
    
    def find_module_in_text(self, text: str) -> Optional[str]:
        text = text.lower()
        
        for module_id, synonyms in TARGET_SYNONYMS.items():
            for synonym in synonyms:
                if synonym.lower() in text:
                    return module_id
        
        return None
    
    def parse_period(self, period_text: str) -> Dict[str, str]:
        if not period_text:
            return {"start": "", "end": ""}
        
        months = {
            "январ": ("01", 31),
            "феврал": ("02", 28),
            "март": ("03", 31),
            "апрел": ("04", 30),
            "май": ("05", 31),
            "мае": ("05", 31),
            "июн": ("06", 30),
            "июл": ("07", 31),
            "август": ("08", 31),
            "сентябр": ("09", 30),
            "октябр": ("10", 31),
            "ноябр": ("11", 30),
            "декабр": ("12", 31)
        }
        
        text = period_text.lower().replace("за ", "")
        current_year = str(datetime.now().year)
        
        for month_prefix, (month_num, last_day) in months.items():
            if month_prefix in text:
                start_date = f"01.{month_num}.{current_year}"
                end_date = f"{last_day}.{month_num}.{current_year}"
                return {"start": start_date, "end": end_date}
        
        return {"start": "", "end": ""}
    
    def extract_entities(self, ner_results: List[Dict[str, str]]) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        entities = {}
        raw_tokens = []
        current_entity = None
        entity_tokens = []
        
        for item in ner_results:
            tag = item["tag"]
            token = item["token"]
            
            raw_tokens.append({"token": token, "tag": tag})
            
            if tag == "O":
                if current_entity and entity_tokens:
                    entities[current_entity] = " ".join(entity_tokens)
                    current_entity = None
                    entity_tokens = []
                continue
            
            if tag.startswith("B-"):
                if current_entity and entity_tokens:
                    entities[current_entity] = " ".join(entity_tokens)
                
                entity_type = tag[2:]
                current_entity = entity_type
                entity_tokens = [token]
            
            elif tag.startswith("I-"):
                if current_entity and tag[2:] == current_entity:
                    entity_tokens.append(token)
        
        if current_entity and entity_tokens:
            entities[current_entity] = " ".join(entity_tokens)
        
        return entities, raw_tokens
    
    def process_command(self, text: str, ner_results: List[Dict[str, str]]) -> Dict[str, Any]:
        entities, raw_tokens = self.extract_entities(ner_results)
        
        result = {
            "connectionId": "",
            "parameters": {
                "wellId": "",
                "wellField": "",
                "wellName": "",
                "period": {
                    "start": "",
                    "end": ""
                },
                "moduleName": "",
                "moduleID": ""
            },
            "command": "UNKNOWN",
            "debug": {
                "raw_tokens": raw_tokens,
                "entities_found": list(entities.keys()),
                "text_processed": text
            }
        }
        
        if "WELL_FIELD" in entities:
            result["parameters"]["wellField"] = entities["WELL_FIELD"]
        
        if "WELL_NAME" in entities:
            result["parameters"]["wellName"] = entities["WELL_NAME"]
        
        if "PERIOD" in entities:
            period_dates = self.parse_period(entities["PERIOD"])
            result["parameters"]["period"] = period_dates
        
        # Ищем модуль
        module_id = None
        
        # 1. Сначала по сущности TARGET
        if "TARGET" in entities:
            module_id = self.find_module_by_target(entities["TARGET"])
        
        # 2. Если не нашли, по всему тексту
        if not module_id:
            module_id = self.find_module_in_text(text.lower())
        
        # 3. Если всё ещё не нашли, по контексту
        if not module_id:
            if any(keyword in text.lower() for keyword in ["шахмат", "шахматк"]):
                module_id = "Ois.Modules.chessy.ChessyModule"
            elif any(keyword in text.lower() for keyword in ["отчет", "сводк", "доклад"]):
                module_id = "standalone_report"
            elif any(keyword in text.lower() for keyword in ["форму", "ввод"]):
                module_id = "forms_input_engine"
        
        # Заполняем информацию о модуле
        if module_id and module_id in self.registry:
            result["parameters"]["moduleName"] = module_id
            result["command"] = self.registry[module_id]["intent"]
        
        # Добавляем entities в debug информацию
        result["debug"]["entities"] = entities
        
        return result
    
    # Rule-based метод тоже с raw токенами
    @staticmethod
    def rule_based_processor(text: str) -> Dict[str, Any]:
        """Процессор на основе правил с raw токенами"""
        text_lower = text.lower()
        
        # Создаем raw токены на основе простого разбиения
        raw_tokens = []
        words = text.split()
        for word in words:
            raw_tokens.append({
                "token": word,
                "tag": "O"  # По умолчанию все O для rule-based
            })
        
        result = {
            "connectionId": "",
            "parameters": {
                "wellId": "",
                "wellField": "",
                "wellName": "",
                "period": {"start": "", "end": ""},
                "moduleName": "",
                "moduleID": ""
            },
            "command": "UNKNOWN",
            "debug": {
                "raw_tokens": raw_tokens,
                "entities_found": [],
                "text_processed": text,
                "method": "rule_based"
            }
        }
        
        if "шахмат" in text_lower:
            result["parameters"]["moduleName"] = "Ois.Modules.chessy.ChessyModule"
            result["command"] = "OPEN_MODULE"
            result["debug"]["entities_found"].append("TARGET")
        
        well_fields = ["самотлор", "приобское", "ванкор", "вишанское", "уренгойское", 
                       "ямбургское", "бованенково", "юрубчено", "чаяндинское"]
        entities = {}
        for field in well_fields:
            if field in text_lower:
                result["parameters"]["wellField"] = field.capitalize()
                result["debug"]["entities_found"].append("WELL_FIELD")
                entities["WELL_FIELD"] = field.capitalize()
                break
        
        matches = re.findall(r'\b\d+[А-Яа-я]?\b', text)
        if matches:
            result["parameters"]["wellName"] = matches[0]
            result["debug"]["entities_found"].append("WELL_NAME")
            entities["WELL_NAME"] = matches[0]
        
        month_patterns = {
            "январ": ("01", 31),
            "феврал": ("02", 28),
            "март": ("03", 31),
            "апрел": ("04", 30),
            "май": ("05", 31),
            "июн": ("06", 30),
            "июл": ("07", 31),
            "август": ("08", 31),
            "сентябр": ("09", 30),
            "октябр": ("10", 31),
            "ноябр": ("11", 30),
            "декабр": ("12", 31)
        }
        
        current_year = str(datetime.now().year)
        for month_key, (month_num, last_day) in month_patterns.items():
            if month_key in text_lower:
                result["parameters"]["period"] = {
                    "start": f"01.{month_num}.{current_year}",
                    "end": f"{last_day}.{month_num}.{current_year}"
                }
                result["debug"]["entities_found"].append("PERIOD")
                entities["PERIOD"] = f"за {month_key}"
                break
        
        result["debug"]["entities"] = entities
        return result