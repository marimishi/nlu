import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from .constants import TARGET_SYNONYMS, REGISTRY, INTENTS, WELL_FIELDS
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
    
    def determine_entity_order(self, text: str, entities: Dict[str, str]) -> Dict[str, str]:
        """
        Определяет порядок сущностей в тексте и корректирует их значения.
        Обрабатывает случаи типа '850 покачевское' (номер скважины + месторождение).
        """
        text_lower = text.lower()
        corrected_entities = entities.copy()
        
        # Проверяем комбинацию WELL_NAME + WELL_FIELD
        if "WELL_NAME" in entities and "WELL_FIELD" in entities:
            well_name = entities["WELL_NAME"]
            well_field = entities["WELL_FIELD"]
            
            # Ищем позиции в тексте
            well_name_pos = text_lower.find(well_name.lower())
            well_field_pos = text_lower.find(well_field.lower())
            
            # Если WELL_NAME перед WELL_FIELD и они близко друг к другу
            if well_name_pos != -1 and well_field_pos != -1:
                # Определяем расстояние между ними
                distance = abs(well_field_pos - (well_name_pos + len(well_name)))
                
                # Если они идут подряд или близко (типичный случай "850 покачевское")
                if distance < 3:  # Допустимый промежуток в символах
                    # Проверяем, не является ли WELL_NAME частью WELL_FIELD
                    
                    # Проверяем, что well_name выглядит как номер скважины (содержит цифры)
                    if any(c.isdigit() for c in well_name) and not any(c.isdigit() for c in well_field):
                        # Это типичный случай: "850 покачевское"
                        # Сохраняем как есть, порядок уже правильный
                        pass
                    else:
                        # Возможно, это наоборот: "самотлор 123А"
                        # В этом случае нужно поменять местами
                        if well_field_pos < well_name_pos:
                            # Меняем местами, так как месторождение перед номером
                            corrected_entities["WELL_NAME"], corrected_entities["WELL_FIELD"] = \
                                corrected_entities["WELL_FIELD"], corrected_entities["WELL_NAME"]
        
        return corrected_entities
    
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
        
        # Определяем правильный порядок сущностей
        entities = self.determine_entity_order(text, entities)
        
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
        
        # Заполняем параметры с учетом порядка сущностей
        if "WELL_FIELD" in entities:
            result["parameters"]["wellField"] = entities["WELL_FIELD"]
        
        if "WELL_NAME" in entities:
            result["parameters"]["wellName"] = entities["WELL_NAME"]
        
        # Дополнительная логика для поиска номеров скважин с префиксами
        text_lower = text.lower()
        
        # Ищем паттерны типа "скв. 850" или "скважина 123А"
        well_patterns = [
            r'скв\.?\s*(\d+[А-Яа-я]?)',
            r'скважина\s*(\d+[А-Яа-я]?)',
            r'№\s*(\d+[А-Яа-я]?)'
        ]
        
        for pattern in well_patterns:
            match = re.search(pattern, text_lower)
            if match:
                well_number = match.group(1)
                # Если NER не нашел WELL_NAME, но мы нашли номер в тексте
                if "WELL_NAME" not in entities or not result["parameters"]["wellName"]:
                    result["parameters"]["wellName"] = well_number
                    entities["WELL_NAME"] = well_number
                break
        
        period_parts = []
        
        # Проверяем TARGET на наличие числительных (дат)
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
        
        # Собираем все части даты/периода
        for entity_type in ["DATE", "MONTH", "YEAR", "PERIOD"]:
            if entity_type in entities:
                period_parts.append(entities[entity_type])
        
        # Парсим период
        if period_parts:
            period_text = " ".join(period_parts)
            period_dates = self.parse_period(period_text)
            if period_dates["start"] and period_dates["end"]:
                result["parameters"]["period"] = period_dates
                result["debug"]["period_parsed"] = {
                    "input": period_text,
                    "output": period_dates
                }
        
        # Поиск модуля
        module_id = None
        
        if "TARGET" in entities:
            target_text = entities["TARGET"]
            # Проверяем, что TARGET не является числительным (датой)
            if not any(num in target_text.lower() for num in [
                "первое", "второе", "третье", "четвертое", "пятое",
                "шестое", "седьмое", "восьмое", "девятое", "десятое"
            ]):
                module_id = self.find_module_by_target(target_text)
        
        # Если не нашли по TARGET, ищем во всем тексте
        if not module_id:
            module_id = self.find_module_in_text(text.lower())
        
        # Фолбэк логика по ключевым словам
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
        
        # Заполняем информацию о модуле
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
        
        # ОБНОВЛЕННАЯ ЛОГИКА ДЛЯ ПОИСКА СКВАЖИН И МЕСТОРОЖДЕНИЙ
        # Сначала ищем паттерны с комбинациями
        well_patterns = [
            (r'по\s+(\d+[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),  # "по 850 покачевское"
            (r'(\d+[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),        # "850 покачевское"
            (r'скв\.?\s*(\d+[А-Яа-я]?)', 1),                 # "скв. 850"
            (r'скважина\s*(\d+[А-Яа-я]?)', 1),               # "скважина 123А"
            (r'№\s*(\d+[А-Яа-я]?)', 1),                      # "№ 45"
        ]
        
        well_found = False
        for pattern, groups in well_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if isinstance(groups, tuple):
                    # Паттерн с двумя группами (номер и месторождение)
                    well_number = match.group(groups[0])
                    well_field_candidate = match.group(groups[1])
                    
                    # Проверяем, является ли кандидат месторождением
                    well_fields_lower = [f.lower() for f in WELL_FIELDS]
                    
                    # Также проверяем с суффиксом (например "покачевское")
                    well_field_candidate_with_suffix = well_field_candidate
                    if not well_field_candidate.endswith(('ое', 'ее', 'ая', 'яя')):
                        well_field_candidate_with_suffix = well_field_candidate + 'ое'
                    
                    candidate_found = None
                    for field in well_fields_lower:
                        if (well_field_candidate == field or 
                            well_field_candidate_with_suffix == field or
                            field.startswith(well_field_candidate)):
                            candidate_found = field
                            break
                    
                    if candidate_found:
                        result["parameters"]["wellName"] = well_number
                        result["parameters"]["wellField"] = candidate_found.capitalize()
                        entities["WELL_NAME"] = well_number
                        entities["WELL_FIELD"] = candidate_found.capitalize()
                        well_found = True
                        break
                else:
                    # Просто номер скважины
                    well_number = match.group(groups)
                    result["parameters"]["wellName"] = well_number
                    entities["WELL_NAME"] = well_number
                    well_found = True
                    # Продолжаем поиск месторождения отдельно
                    break
        
        # Если не нашли через паттерны с комбинациями, используем раздельную логику
        if not well_found:
            # Поиск месторождений
            well_fields_lower = [f.lower() for f in WELL_FIELDS]
            for field in well_fields_lower:
                if field in text_lower:
                    result["parameters"]["wellField"] = field.capitalize()
                    entities["WELL_FIELD"] = field.capitalize()
                    break
            
            # Поиск номеров скважин (исключая годы)
            matches = re.findall(r'\b\d+[А-Яа-я]?\b', text)
            if matches:
                for match in matches:
                    # Проверяем, что это не год
                    if not (len(match) == 4 and match.isdigit() and 1900 <= int(match) <= 2100):
                        result["parameters"]["wellName"] = match
                        entities["WELL_NAME"] = match
                        break
        
        # Определение модуля и команды
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
        elif any(keyword in text_lower for keyword in ["форму", "ввод"]):
            result["parameters"]["moduleName"] = "forms_input_engine"
            result["command"] = "OPEN_MODULE"
            entities["TARGET"] = "форма"
        elif "режим" in text_lower:
            result["parameters"]["moduleName"] = "mode_output"
            result["command"] = "OPEN_MODULE"
            entities["TARGET"] = "режим"
        elif "баланс" in text_lower:
            result["parameters"]["moduleName"] = "volume_balance"
            result["command"] = "OPEN_MODULE"
            entities["TARGET"] = "баланс"
        elif any(keyword in text_lower for keyword in ["отчетность", "движок отчет"]):
            result["parameters"]["moduleName"] = "reporting_engine"
            result["command"] = "OPEN_MODULE"
            entities["TARGET"] = "отчетность"
        
        # Обработка периода/даты
        period_dates = {"start": "", "end": ""}
        
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
            # Ищем период с помощью регулярных выражений
            period_match = re.search(r'за\s+(.+?)(?:\s|$)', text_lower)
            if period_match:
                period_text = period_match.group(1)
                entities["PERIOD"] = period_text
                period_dates = date_parser.parse_period(period_text)
            else:
                # Проверяем наличие месяцев в тексте
                months = [
                    "январь", "февраль", "март", "апрель", "май", "июнь",
                    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
                ]
                for month in months:
                    if month in text_lower:
                        entities["MONTH"] = month
                        period_dates = date_parser.parse_period(month)
                        break
        
        if period_dates["start"] and period_dates["end"]:
            result["parameters"]["period"] = period_dates
        
        # Ищем год отдельно
        year_match = re.search(r'(20\d{2})', text)
        if year_match:
            entities["YEAR"] = year_match.group(1)
            # Если уже есть период, добавляем к нему год
            if result["parameters"]["period"]["start"]:
                # Парсим заново с годом
                if "PERIOD" in entities:
                    period_text = entities["PERIOD"] + " " + year_match.group(1)
                    period_dates = date_parser.parse_period(period_text)
                    if period_dates["start"]:
                        result["parameters"]["period"] = period_dates
        
        result["debug"]["entities"] = entities
        result["debug"]["entities_found"] = list(entities.keys())
        
        return result