import re
from typing import Dict, Any, List

from core.nlu.parsers.entity_parser import EntityParser
from core.nlu.parsers.date_parser import date_parser
from core.registry.registry_service import RegistryService
from core.command.command import NLUCommand
from config.command_config import WELL_FIELDS


class CommandProcessor:
    def __init__(self, registry_service: RegistryService):
        self.registry_service = registry_service
        self.entity_parser = EntityParser()
    
    def process_command(self, text: str, ner_results: List[Dict[str, str]]) -> Dict[str, Any]:
        entities, raw_tokens = self.entity_parser.extract_entities(ner_results)
        
        entities = self.entity_parser.determine_entity_order(text, entities)
        
        command = NLUCommand.create_from_analysis(text, entities, method="ner")
        command.debug_info["raw_tokens"] = raw_tokens
        command.debug_info["entities_found"] = list(entities.keys())
        
        if "WELL_FIELD" in entities:
            command.parameters["wellField"] = entities["WELL_FIELD"]
        
        if "WELL_NAME" in entities:
            command.parameters["wellName"] = entities["WELL_NAME"]
        
        text_lower = text.lower()
        well_patterns = [
            r'скв\.?\s*(\d+[А-Яа-я]?)',
            r'скважина\s*(\d+[А-Яа-я]?)',
            r'№\s*(\d+[А-Яа-я]?)'
        ]
        
        for pattern in well_patterns:
            match = re.search(pattern, text_lower)
            if match:
                well_number = match.group(1)
                if "WELL_NAME" not in entities or not command.parameters["wellName"]:
                    command.parameters["wellName"] = well_number
                    entities["WELL_NAME"] = well_number
                break
        
        period_dates = self.entity_parser.parse_period_from_entities(entities)
        if period_dates["start"] and period_dates["end"]:
            command.parameters["period"] = period_dates
            command.debug_info["period_parsed"] = {
                "input": " ".join([entities.get(k, "") for k in ["DATE", "MONTH", "YEAR", "PERIOD"] if k in entities]),
                "output": period_dates
            }
        
        module_id = None
        
        if "TARGET" in entities:
            target_text = entities["TARGET"]
            if not any(num in target_text.lower() for num in [
                "первое", "второе", "третье", "четвертое", "пятое",
                "шестое", "седьмое", "восьмое", "девятое", "десятое"
            ]):
                module_id = self.registry_service.find_module_by_target(target_text)
        
        if not module_id:
            module_id = self.registry_service.find_module_in_text(text.lower())
        
        if not module_id:
            module_id = self._fallback_module_detection(text.lower())
        
        if module_id:
            module_info = self.registry_service.get_module_registry(module_id)
            command.parameters["moduleName"] = module_id
            command.parameters["moduleID"] = module_id
            command.command = module_info.get("intent", "UNKNOWN")
        
        command.debug_info["entities"] = entities
        
        return command.to_dict()
    
    def rule_based_processor(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        raw_tokens = []
        words = text.split()
        for word in words:
            raw_tokens.append({
                "token": word,
                "tag": "O"
            })
        
        command = NLUCommand.create_from_analysis(text, {}, method="rule_based")
        command.debug_info["raw_tokens"] = raw_tokens
        
        entities = self.entity_parser.find_well_entities_by_rules(text)
        
        if "WELL_FIELD" in entities:
            command.parameters["wellField"] = entities["WELL_FIELD"]
        
        if "WELL_NAME" in entities:
            command.parameters["wellName"] = entities["WELL_NAME"]
        
        module_id = self._detect_module_by_keywords(text_lower)
        if module_id:
            module_info = self.registry_service.get_module_registry(module_id)
            command.parameters["moduleName"] = module_id
            command.parameters["moduleID"] = module_id
            command.command = module_info.get("intent", "UNKNOWN")
            entities["TARGET"] = self._get_target_name_by_module(module_id)
        
        period_dates = self._parse_period_rule_based(text_lower)
        if period_dates["start"] and period_dates["end"]:
            command.parameters["period"] = period_dates
        
        command.debug_info["entities"] = entities
        command.debug_info["entities_found"] = list(entities.keys())
        
        return command.to_dict()
    
    def _fallback_module_detection(self, text: str) -> str:
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ["шахмат", "шахматк"]):
            return "Ois.Modules.chessy.ChessyModule"
        elif any(keyword in text_lower for keyword in ["отчет", "сводк", "доклад"]):
            return "standalone_report"
        elif any(keyword in text_lower for keyword in ["форму", "ввод"]):
            return "forms_input_engine"
        elif any(keyword in text_lower for keyword in ["данные", "конструкц"]):
            return "well_construction"
        elif "режим" in text_lower:
            return "mode_output"
        elif "баланс" in text_lower:
            return "volume_balance"
        return None
    
    def _detect_module_by_keywords(self, text_lower: str) -> str:
        if any(keyword in text_lower for keyword in ["шахмат", "шахматк"]):
            return "Ois.Modules.chessy.ChessyModule"
        elif any(keyword in text_lower for keyword in ["отчет", "сводк", "доклад"]):
            return "standalone_report"
        elif any(keyword in text_lower for keyword in ["данные", "конструкц"]):
            return "well_construction"
        elif any(keyword in text_lower for keyword in ["форму", "ввод"]):
            return "forms_input_engine"
        elif "режим" in text_lower:
            return "mode_output"
        elif "баланс" in text_lower:
            return "volume_balance"
        elif any(keyword in text_lower for keyword in ["отчетность", "движок отчет"]):
            return "reporting_engine"
        return None
    
    def _get_target_name_by_module(self, module_id: str) -> str:
        target_names = {
            "Ois.Modules.chessy.ChessyModule": "шахматка",
            "standalone_report": "отчет",
            "well_construction": "данные",
            "forms_input_engine": "форма",
            "mode_output": "режим",
            "volume_balance": "баланс",
            "reporting_engine": "отчетность"
        }
        return target_names.get(module_id, "")
    
    def _parse_period_rule_based(self, text_lower: str) -> Dict[str, str]:
        if "прошлый месяц" in text_lower or "предыдущий месяц" in text_lower or "последний месяц" in text_lower:
            return date_parser.parse_period("прошлый месяц")
        elif "текущий месяц" in text_lower or "этот месяц" in text_lower:
            return date_parser.parse_period("текущий месяц")
        elif "следующий месяц" in text_lower:
            return date_parser.parse_period("следующий месяц")
        else:
            period_match = re.search(r'за\s+(.+?)(?:\s|$)', text_lower)
            if period_match:
                period_text = period_match.group(1)
                return date_parser.parse_period(period_text)
            else:
                months = [
                    "январь", "февраль", "март", "апрель", "май", "июнь",
                    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
                ]
                for month in months:
                    if month in text_lower:
                        return date_parser.parse_period(month)
        
        return {"start": "", "end": ""}