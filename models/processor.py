import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from .constants import TARGET_SYNONYMS, REGISTRY, INTENTS
from .date_parser import date_parser


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
        return date_parser.parse_period(period_text)
    
    def extract_entities(self, ner_results: List[Dict[str, str]]) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        entities = {}
        raw_tokens = []
        current_entity = None
        entity_tokens = []
        
        for item in ner_results:
            tag = item["tag"]
            token = item["token"]
            
            raw_tokens.append({"token": token, "tag": tag})
            
            if token.lower() == "за":
                if current_entity and entity_tokens:
                    entities[current_entity] = " ".join(entity_tokens)
                current_entity = None
                entity_tokens = []
                continue
            
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
        
        period_parts = []
        
        if "TARGET" in entities:
            target_text = entities["TARGET"].lower()
            if any(num in target_text for num in [
                "первое", "второе", "третье", "четвертое", "пятое",
                "шестое", "седьмое", "восьмое", "девятое", "десятое",
                "одиннадцатое", "двенадцатое", "тринадцатое", 
                "четырнадцатое", "пятнадцатое", "шестнадцатое",
                "семнадцатое", "восемнадцатое", "девятнадцатое",
                "двадцатое", "двадцать", "тридцатое", "тридцать"
            ]):
                period_parts.append(entities["TARGET"])
        
        for entity_type in ["DATE", "MONTH", "YEAR", "PERIOD"]:
            if entity_type in entities:
                period_parts.append(entities[entity_type])
        
        if period_parts:
            period_text = " ".join(period_parts)
            period_dates = self.parse_period(period_text)
            if period_dates["start"] and period_dates["end"]:
                result["parameters"]["period"] = period_dates
                result["debug"]["period_parsed"] = {
                    "input": period_text,
                    "output": period_dates
                }
        
        module_id = None
        
        if "TARGET" in entities:
            target_text = entities["TARGET"]
            if not any(num in target_text.lower() for num in [
                "первое", "второе", "третье", "четвертое", "пятое",
                "шестое", "седьмое", "восьмое", "девятое", "десятое"
            ]):
                module_id = self.find_module_by_target(target_text)
        
        if not module_id:
            module_id = self.find_module_in_text(text.lower())
        
        if not module_id:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in ["шахмат", "шахматк"]):
                module_id = "Ois.Modules.chessy.ChessyModule"
            elif any(keyword in text_lower for keyword in ["отчет", "сводк", "доклад"]):
                module_id = "standalone_report"
            elif any(keyword in text_lower for keyword in ["форму", "ввод"]):
                module_id = "forms_input_engine"
            elif any(keyword in text_lower for keyword in ["данные", "конструкц"]):
                module_id = "well_construction"
            elif "режим" in text_lower:
                module_id = "mode_output"
            elif "баланс" in text_lower:
                module_id = "volume_balance"
        
        if module_id and module_id in self.registry:
            result["parameters"]["moduleName"] = module_id
            result["command"] = self.registry[module_id]["intent"]
        
        result["debug"]["entities"] = entities
        
        return result
    
    @staticmethod
    def rule_based_processor(text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        raw_tokens = []
        words = text.split()
        for word in words:
            raw_tokens.append({
                "token": word,
                "tag": "O"
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
        
        entities = {}
        
        if any(keyword in text_lower for keyword in ["шахмат", "шахматк"]):
            result["parameters"]["moduleName"] = "Ois.Modules.chessy.ChessyModule"
            result["command"] = "OPEN_MODULE"
            entities["TARGET"] = "шахматка"
        elif any(keyword in text_lower for keyword in ["отчет", "сводк", "доклад"]):
            result["parameters"]["moduleName"] = "standalone_report"
            result["command"] = "BUILD_REPORT"
            entities["TARGET"] = "отчет"
        elif any(keyword in text_lower for keyword in ["данные", "конструкц"]):
            result["parameters"]["moduleName"] = "well_construction"
            result["command"] = "OPEN_MODULE"
            entities["TARGET"] = "данные"
        elif "режим" in text_lower:
            result["parameters"]["moduleName"] = "mode_output"
            result["command"] = "OPEN_MODULE"
            entities["TARGET"] = "режим"
        
        well_fields = ["самотлор", "приобское", "ванкор", "вишанское", "уренгойское", 
                    "ямбургское", "бованенково", "юрубчено", "чаяндинское"]
        for field in well_fields:
            if field in text_lower:
                result["parameters"]["wellField"] = field.capitalize()
                entities["WELL_FIELD"] = field.capitalize()
                break
        
        matches = re.findall(r'\b\d+[А-Яа-я]?\b', text)
        if matches:
            result["parameters"]["wellName"] = matches[0]
            entities["WELL_NAME"] = matches[0]
        
        text_lower = text.lower()
        
        if "прошлый месяц" in text_lower or "предыдущий месяц" in text_lower or "последний месяц" in text_lower:
            entities["PERIOD"] = "прошлый месяц"
            period_dates = date_parser.parse_period("прошлый месяц")
        elif "текущий месяц" in text_lower or "этот месяц" in text_lower:
            entities["PERIOD"] = "текущий месяц"
            period_dates = date_parser.parse_period("текущий месяц")
        elif "следующий месяц" in text_lower:
            entities["PERIOD"] = "следующий месяц"
            period_dates = date_parser.parse_period("следующий месяц")
        else:
            period_match = re.search(r'за\s+(.+)', text_lower)
            if period_match:
                period_text = period_match.group(1)
                period_dates = date_parser.parse_period(period_text)
                entities["PERIOD"] = period_text
        
        if period_dates["start"] and period_dates["end"]:
            result["parameters"]["period"] = period_dates
        
        result["debug"]["entities"] = entities
        result["debug"]["entities_found"] = list(entities.keys())
        
        return result