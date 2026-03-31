"""
Модуль обработки команд классификатора Roisa.

Предоставляет класс CommandProcessor для анализа пользовательских запросов,
извлечения сущностей, определения модулей и параметров команд.

Поддерживает два метода обработки:
    - NER-based (Named Entity Recognition) — на основе результатов NER-модели
    - Rule-based — на основе правил и ключевых слов

Основные компоненты:
    - CommandProcessor — основной класс обработки команд
    - Методы извлечения параметров (скважина, месторождение, период)
    - Методы определения модулей по сущностям и ключевым словам
    - Валидация обязательных параметров команды

Пример использования:
    >>> registry_service = RegistryService()
    >>> processor = CommandProcessor(registry_service)
    >>> result = processor.process_command(
    ...     "Открой шахматку Мишаевское 137Р за октябрь",
    ...     ner_results
    ... )
"""
import re
from typing import Any

from ..nlu.parsers.entity_parser import EntityParser  # pylint: disable=relative-beyond-top-level
from ..nlu.parsers.date_parser import date_parser  # pylint: disable=relative-beyond-top-level
from ..nlu.parsers.well_field_normalizer import normalize_well_field
from ..registry.registry_service import RegistryService  # pylint: disable=relative-beyond-top-level
from ..command.command import NLUCommand  # pylint: disable=relative-beyond-top-level
from ...config.command_config import WELL_FIELDS

class CommandProcessor:
    def __init__(self, registry_service: RegistryService):
        self.registry_service = registry_service
        self.entity_parser = EntityParser()
    
    def process_command(self, text: str, ner_results: list[dict[str, str]]) -> dict[str, Any]:
        print(f"Processing command with text: {text}")
        print(f"NER results: {ner_results}")
        
        entities, raw_tokens = self.entity_parser.extract_entities(ner_results)
        
        print(f"Extracted entities: {entities}")
        
        if entities.get("PERIOD") == "года":
            text_lower = text.lower()
            if "прошлого" in text_lower or "прошлый" in text_lower or "прошлом" in text_lower:
                entities["PERIOD"] = "прошлого года"
                print(f"Fixed PERIOD: {entities['PERIOD']}")
        
        if "PERIOD" not in entities:
            month = entities.get("MONTH", "")
            year = entities.get("YEAR", "")
            if month and year:
                entities["PERIOD"] = f"{month} {year}"
                print(f"Created PERIOD from MONTH and YEAR: {entities['PERIOD']}")
            elif month and "прошлого" in text.lower():
                entities["PERIOD"] = f"{month} прошлого года"
                print(f"Created PERIOD from MONTH + прошлого года: {entities['PERIOD']}")
        
        entities = self.entity_parser.determine_entity_order(text, entities)
        
        command = NLUCommand.create_from_analysis(text, entities, method="ner")
        command.debug_info["raw_tokens"] = raw_tokens
        command.debug_info["entities_found"] = list(entities.keys())

        command.parameters = {
            "wellField": "",
            "wellName": "",
            "period": {"start": "", "end": ""},
            "moduleName": "",
            "moduleId": ""
        }

        if "WELL_FIELD" in entities:
            original = entities["WELL_FIELD"]
            normalized = normalize_well_field(original)
            command.parameters["wellField"] = normalized
            
            if normalized != original:
                command.debug_info["well_field_normalized"] = {
                    "original": original,
                    "normalized": normalized
                }

        if "WELL_NAME" in entities:
            command.parameters["wellName"] = entities["WELL_NAME"]
        
        text_lower = text.lower()
        well_patterns = [
            r'скв\.?\s*(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)',
            r'скважина\s*(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)',
            r'№\s*(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)',
            r'(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)\s+скважина',
            r'(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)\s+скв\.?'
        ]
        
        for pattern in well_patterns:
            match = re.search(pattern, text_lower)
            if match:
                well_number = match.group(1)
                if well_number.isdigit() and len(well_number) == 4:
                    year = int(well_number)
                    if 1900 <= year <= 2100:
                        continue
                if "WELL_NAME" not in entities or not command.parameters["wellName"]:
                    command.parameters["wellName"] = well_number
                    entities["WELL_NAME"] = well_number
                    print(f"Found well name by pattern: {well_number}")
                    break
        
        if command.parameters["wellName"] == "года":
            command.parameters["wellName"] = ""
            print("Removed incorrect wellName 'года'")
        
        period_dates = self.entity_parser.parse_period_from_entities(entities)
        if period_dates["start"] and period_dates["end"]:
            command.parameters["period"] = period_dates
            command.debug_info["period_parsed"] = {
                "input": " ".join([entities.get(k, "") for k in ["DATE", "MONTH", "YEAR", "PERIOD"] if k in entities]),
                "output": period_dates
            }
            print(f"Period parsed: {period_dates}")
        
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
            command.module_name = module_id
            command.module_id = module_id if not None and module_id.isdigit() else ''
            command.module_title = module_info.get("moduleTitle", "")
            command.command = module_info.get("intent", "UNKNOWN")
            slots = module_info.get("slots", {})

            if not slots:
                command.parameters = None
            else:
                command.parameters = {
                    "wellField": command.parameters.get("wellField", ""),
                    "wellName": command.parameters.get("wellName", ""),
                    "period": command.parameters.get("period", {"start": "", "end": ""})
                }

                required_slots = [slot for slot, info in slots.items() if info.get("required", False)]
                slot_to_param = {
                    "WELL_FIELD": "wellField",
                    "WELL_NAME": "wellName",
                    "PERIOD": "period"
                }
                all_required_filled = True
                for slot in required_slots:
                    param_key = slot_to_param.get(slot)
                    if param_key:
                        if param_key == "period":
                            if not command.parameters[param_key]["start"] or not command.parameters[param_key]["end"]:
                                all_required_filled = False
                                break
                        elif not command.parameters[param_key]:
                            all_required_filled = False
                            break

                if not all_required_filled:
                    command.parameters = None
        else:
            command.parameters = None

        command.debug_info["entities"] = entities

        return command.to_dict()
    
    def rule_based_processor(self, text: str) -> dict[str, Any]:
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
            original = entities["WELL_FIELD"]
            normalized = normalize_well_field(original)
            command.parameters["wellField"] = normalized
            
            if normalized != original:
                command.debug_info["well_field_normalized"] = {
                    "original": original,
                    "normalized": normalized
                }
        
        if "WELL_NAME" in entities:
            command.parameters["wellName"] = entities["WELL_NAME"]
        
        module_id = self._detect_module_by_keywords(text_lower)
        if module_id:
            module_info = self.registry_service.get_module_registry(module_id)
            command.module_name = module_id
            command.module_id = module_id if not None and module_id.isdigit() else ''
            command.command = module_info.get("intent", "UNKNOWN")
            entities["TARGET"] = self._get_target_name_by_module(module_id)
            slots = module_info.get("slots", {})

            if not slots:
                command.parameters = None
            else:
                command.parameters = {
                    "wellField": command.parameters.get("wellField", ""),
                    "wellName": command.parameters.get("wellName", ""),
                    "period": command.parameters.get("period", {"start": "", "end": ""})
                }

                required_slots = [slot for slot, info in slots.items() if info.get("required", False)]
                slot_to_param = {
                    "WELL_FIELD": "wellField",
                    "WELL_NAME": "wellName",
                    "PERIOD": "period"
                }
                all_required_filled = True
                for slot in required_slots:
                    param_key = slot_to_param.get(slot)
                    if param_key:
                        if param_key == "period":
                            if not command.parameters[param_key]["start"] or not command.parameters[param_key]["end"]:
                                all_required_filled = False
                                break
                        elif not command.parameters[param_key]:
                            all_required_filled = False
                            break

                if not all_required_filled:
                    command.parameters = None
        else:
            command.parameters = None

        period_dates = self._parse_period_rule_based(text_lower)
        if period_dates["start"] and period_dates["end"] and command.parameters is not None:
            command.parameters["period"] = period_dates

        command.debug_info["entities"] = entities
        command.debug_info["entities_found"] = list(entities.keys())

        return command.to_dict()

    def is_usoi_module(self, module_id: str | None) -> bool:
        """
        Проверяет, является ли модуль USOI.

        Args:
            module_id (str): Идентификатор модуля

        Returns:
            bool: True, если модуль является USOI, иначе False
        """
        return module_id in [
            "10054",
            "10037",
            "10038",
            "10039",
            "10040",
            "10041",
            "10031",
            "10042",
            "10043",
            "10044",
            "10045",
            "10046",
            "10048",
            "10050",
            "10052",
            "10056",
            "10058",
            "10060",
            "10062",
            "10064"]

    def get_module_name(self, module_id: str | None = None) -> str | None:
        """
        Получает имя модуля по его идентификатору.

        Args:
            module_id (str): Идентификатор модуля

        Returns:
            str: Имя модуля, или пустая строка, если модуль не найден
        """
        if self.is_usoi_module(module_id):
            return "ois_usoi"
        return module_id

    def _fallback_module_detection(self, text: str) -> str:
        text_lower = text.lower()
        
        formula_exceptions = ["формул", "формулы", "формулу", "формула", "формуле", "формулой"]
        
        for exception in formula_exceptions:
            if exception in text_lower:
                print(f"Found formula-related word: '{exception}', returning UNKNOWN")
                return None
        
        if any(keyword in text_lower for keyword in ["шахмат", "шахматк"]):
            return "Ois.Modules.chessy.ChessyModule"
        elif any(keyword in text_lower for keyword in ["отчет", "сводк", "доклад"]):
            return "standalone_report"
        elif any(keyword in text_lower for keyword in ["форму", "ввод"]):
            words = text_lower.split()
            if "форму" in words or "форма" in words or "форме" in words:
                return "forms_input_engine"
            elif " форму " in f" {text_lower} " or text_lower.startswith("форму ") or text_lower.endswith(" форму"):
                return "forms_input_engine"
        elif any(keyword in text_lower for keyword in ["данные", "конструкц"]):
            return "well_construction"
        elif "режим" in text_lower:
            return "mode_output"
        elif "баланс" in text_lower:
            return "volume_balance"
        return None

    def _detect_module_by_keywords(self, text_lower: str) -> str:
        formula_exceptions = ["формул", "формулы", "формулу", "формула", "формуле", "формулой"]
        
        for exception in formula_exceptions:
            if exception in text_lower:
                print(f"Found formula-related word: '{exception}', returning UNKNOWN")
                return None
        
        if any(keyword in text_lower for keyword in ["шахмат", "шахматк"]):
            return "Ois.Modules.chessy.ChessyModule"
        elif any(keyword in text_lower for keyword in ["отчет", "сводк", "доклад"]):
            return "standalone_report"
        elif any(keyword in text_lower for keyword in ["данные", "конструкц"]):
            return "well_construction"
        elif any(keyword in text_lower for keyword in ["форму", "ввод"]):
            words = text_lower.split()
            if "форму" in words or "форма" in words or "форме" in words:
                return "forms_input_engine"
            elif " форму " in f" {text_lower} " or text_lower.startswith("форму ") or text_lower.endswith(" форму"):
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
    
    def _parse_period_rule_based(self, text_lower: str) -> dict[str, str]:
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