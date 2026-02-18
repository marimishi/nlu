import re
from typing import Dict, Any, Optional, List, Tuple, Set
from collections import defaultdict

from core.nlu.parsers.date_parser import date_parser
from config.command_config import WELL_FIELDS, WELL_FIELDS_LOWER


class EntityParser:
    def __init__(self):
        self._init_search_structures()
        
        # Слова, которые никогда не должны быть частью WELL_NAME
        self.well_name_stop_words = {
            "года", "год", "г.", "лет", "месяц", "месяца", "месяцев",
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря",
            "первого", "второго", "третьего", "четвертого", "пятого",
            "шестого", "седьмого", "восьмого", "девятого", "десятого"
        }
        
        # Паттерны для валидации номера скважины
        self.well_name_pattern = re.compile(r'^(\d+[А-Яа-я]?|\d+/\d+[А-Яа-я]?)$')
    
    def _init_search_structures(self):
        self.prefix_map = defaultdict(list)
        self.exact_map = {}
        self.part_map = defaultdict(list)
        
        for i, field in enumerate(WELL_FIELDS):
            field_lower = field.lower()
            self.exact_map[field_lower] = field
            
            if len(field_lower) >= 3:
                prefix = field_lower[:3]
                self.prefix_map[prefix].append(field)
            
            words = re.split(r'[-\s]+', field_lower)
            for word in words:
                if len(word) >= 3:
                    self.part_map[word].append(field)
    
    def find_well_field_fast(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        
        for field in WELL_FIELDS:
            if field.lower() in text_lower:
                pattern = r'\b' + re.escape(field.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    return field
        
        words = text_lower.split()
        for word in words:
            if len(word) >= 3:
                prefix = word[:3]
                if prefix in self.prefix_map:
                    candidates = self.prefix_map[prefix]
                    for candidate in candidates:
                        if candidate.lower().startswith(word):
                            return candidate
        
        return None
    
    def determine_entity_order(self, text: str, entities: Dict[str, str]) -> Dict[str, str]:
        """Определяет правильный порядок сущностей на основе их позиции в тексте"""
        text_lower = text.lower()
        corrected_entities = entities.copy()
        
        if "WELL_NAME" in entities and "WELL_FIELD" in entities:
            well_name = entities["WELL_NAME"]
            well_field = entities["WELL_FIELD"]
            
            well_name_pos = text_lower.find(well_name.lower())
            well_field_pos = text_lower.find(well_field.lower())
            
            if well_name_pos != -1 and well_field_pos != -1:
                if well_field_pos < well_name_pos:
                    pass  # Нормальный порядок
                else:
                    # Возможная ошибка - меняем местами
                    if not self._is_valid_well_name(well_name):
                        corrected_entities["WELL_NAME"], corrected_entities["WELL_FIELD"] = \
                            corrected_entities["WELL_FIELD"], corrected_entities["WELL_NAME"]
        
        return corrected_entities
    
    def _is_valid_well_name(self, well_name: str) -> bool:
        """Проверяет, является ли строка валидным номером скважины"""
        # Проверка на стоп-слова
        if well_name.lower() in self.well_name_stop_words:
            return False
        
        # Проверка на длину (слишком длинные строки - не номера скважин)
        if len(well_name) > 15:
            return False
        
        # Проверка на паттерн (должен содержать цифры)
        if not any(c.isdigit() for c in well_name):
            return False
        
        # Проверка, что это не дата
        if well_name.lower() in {"две", "тысячи", "двадцать", "пятого"}:
            return False
        
        return True
    
    def extract_entities(self, ner_results: List[Dict[str, str]]) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        """Извлекает сущности с умной пост-обработкой"""
        entities = {}
        raw_tokens = []
        current_entity = None
        entity_tokens = []
        
        # Первый проход - собираем все сущности
        for i, item in enumerate(ner_results):
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
        
        # Не забываем последнюю сущность
        if current_entity and entity_tokens:
            entities[current_entity] = " ".join(entity_tokens)
        
        # Специальная обработка для PERIOD - объединяем несколько частей
        period_parts = []
        for key in list(entities.keys()):
            if key == "PERIOD":
                period_parts.append(entities[key])
            elif key in ["DATE", "MONTH", "YEAR"]:
                period_parts.append(entities[key])
        
        if period_parts:
            # Удаляем дубликаты и объединяем
            unique_parts = []
            for part in period_parts:
                if part not in unique_parts:
                    unique_parts.append(part)
            
            # Проверяем, не потеряли ли мы относительные периоды
            text_lower = " ".join(unique_parts).lower()
            if "прошл" in text_lower or "предыдущ" in text_lower or "последн" in text_lower:
                # Уже есть относительный период, оставляем как есть
                pass
            elif any(word in text_lower for word in ["прошлого", "предыдущего", "последнего"]):
                # Добавляем недостающее слово
                pass
            
            entities["PERIOD"] = " ".join(unique_parts)
        
        return entities, raw_tokens
    
    def parse_period_from_entities(self, entities: Dict[str, str]) -> Dict[str, str]:
        """Парсит период из сущностей с учетом контекста"""
        period_parts = []
        
        # Сначала ищем явные сущности периода
        if "PERIOD" in entities:
            period_text = entities["PERIOD"]
            # Проверяем, не потеряли ли мы часть периода
            if period_text == "года" and "прошлого" in str(entities):
                # Ищем "прошлого" в других сущностях
                for key, value in entities.items():
                    if "прошлого" in value.lower():
                        period_parts.append(value)
                        break
                else:
                    # Если не нашли, добавляем "прошлого года" вручную
                    period_parts.append("прошлого года")
            else:
                period_parts.append(period_text)
        
        if "YEAR" in entities:
            year = entities["YEAR"]
            # Проверяем, что год - это действительно год
            if year.isdigit() and len(year) == 4 and 1900 <= int(year) <= 2100:
                period_parts.append(year)
        
        if "DATE" in entities:
            period_parts.append(entities["DATE"])
        
        # Проверяем TARGET на наличие дат (числа)
        if "TARGET" in entities:
            target_text = entities["TARGET"].lower()
            date_numerals = [
                "первое", "второе", "третье", "четвертое", "пятое",
                "шестое", "седьмое", "восьмое", "девятое", "десятое",
                "одиннадцатое", "двенадцатое", "тринадцатое", 
                "четырнадцатое", "пятнадцатое", "шестнадцатое",
                "семнадцатое", "восемнадцатое", "девятнадцатое",
                "двадцатое", "двадцать", "тридцатое", "тридцать"
            ]
            
            if any(num in target_text for num in date_numerals):
                # Извлекаем только число, не весь TARGET
                for num in date_numerals:
                    if num in target_text:
                        period_parts.append(num)
                        break
        
        if period_parts:
            period_text = " ".join(period_parts)
            print(f"Parsing period from: '{period_text}'")
            
            # Специальная обработка для относительных периодов
            if "прошлого года" in period_text.lower() or "прошлый год" in period_text.lower():
                # Перенаправляем на правильную обработку
                return date_parser.parse_period("прошлый год")
            
            return date_parser.parse_period(period_text)
        
        return {"start": "", "end": ""}
    
    def find_well_entities_by_rules(self, text: str) -> Dict[str, str]:
        """Находит сущности скважины по правилам (fallback метод)"""
        entities = {}
        text_lower = text.lower()
        
        well_field = self.find_well_field_fast(text)
        if well_field:
            entities["WELL_FIELD"] = well_field
            print(f"Found well field by fast search: {well_field}")
        
        # Улучшенные паттерны для поиска номера скважины
        well_patterns = [
            (r'по\s+(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),  # "по 850 покачевское"
            (r'(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),      # "850 покачевское"
            (r'скв\.?\s*(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)', 1),               # "скв. 850"
            (r'скважина\s*(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)', 1),             # "скважина 123А"
            (r'№\s*(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)', 1),                    # "№ 45"
            (r'(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)\s+(скважина|скв\.?)', (1, None)),  # "850 скважина"
        ]
        
        for pattern, groups in well_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if isinstance(groups, tuple):
                    well_number = match.group(groups[0])
                    
                    # Валидация номера скважины
                    if self._is_valid_well_name(well_number):
                        entities["WELL_NAME"] = well_number
                        
                        # Ищем месторождение
                        if groups[1] is not None and "WELL_FIELD" not in entities:
                            well_field_candidate = match.group(groups[1])
                            candidate_field = self._check_well_field_candidate(well_field_candidate)
                            if candidate_field:
                                entities["WELL_FIELD"] = candidate_field
                        
                        return entities
                else:
                    well_number = match.group(groups)
                    if self._is_valid_well_name(well_number):
                        entities["WELL_NAME"] = well_number
                        return entities
        
        # Если не нашли по паттернам, ищем отдельные числа
        if "WELL_NAME" not in entities:
            # Ищем числа, которые не являются годами
            matches = re.findall(r'\b(\d+[А-Яа-я]?)\b', text)
            for match in matches:
                # Проверяем, что это не год
                if len(match) == 4 and match.isdigit():
                    year = int(match)
                    if 1900 <= year <= 2100:
                        continue
                
                # Проверяем, что это не часть даты
                context_before = text_lower[:text_lower.find(match.lower())]
                if "за" in context_before or "в" in context_before:
                    # Может быть частью даты, проверяем следующий контекст
                    context_after = text_lower[text_lower.find(match.lower()) + len(match):]
                    if any(month in context_after for month in ["январь", "февраль", "март"]):
                        continue
                
                entities["WELL_NAME"] = match
                break
        
        return entities
    
    def _check_well_field_candidate(self, candidate: str) -> Optional[str]:
        """Проверяет кандидата на месторождение"""
        candidate_lower = candidate.lower()
        
        if candidate_lower in self.exact_map:
            return self.exact_map[candidate_lower]
        
        suffixes = ['ое', 'ее', 'ая', 'яя']
        for suffix in suffixes:
            candidate_with_suffix = candidate_lower + suffix
            if candidate_with_suffix in self.exact_map:
                return self.exact_map[candidate_with_suffix]
        
        if candidate_lower in self.part_map:
            candidates = self.part_map[candidate_lower]
            return candidates[0] if candidates else None
        
        return None