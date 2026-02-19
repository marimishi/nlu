import re
from typing import Dict, Any, Optional, List, Tuple, Set
from collections import defaultdict

from core.nlu.parsers.date_parser import date_parser
from config.command_config import WELL_FIELDS, WELL_FIELDS_LOWER


class EntityParser:
    def __init__(self):
        self._init_search_structures()
        
        self.well_name_stop_words = {
            "года", "год", "г.", "лет", "месяц", "месяца", "месяцев",
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря",
            "первого", "второго", "третьего", "четвертого", "пятого",
            "шестого", "седьмого", "восьмого", "девятого", "десятого"
        }
        
        self.well_name_pattern = re.compile(r'^(\d+[А-Яа-я]?|\d+/\d+[А-Яа-я]?)$')
        
        self.relative_period_words = {
            "прошлый", "прошлого", "прошлом", "предыдущий", "предыдущего", 
            "последний", "последнего", "текущий", "текущего", "этот", "этого",
            "следующий", "следующего", "будущий", "будущего"
        }
        
        self.month_words = {
            "январь", "января", "февраль", "февраля", "март", "марта",
            "апрель", "апреля", "май", "мая", "июнь", "июня",
            "июль", "июля", "август", "августа", "сентябрь", "сентября",
            "октябрь", "октября", "ноябрь", "ноября", "декабрь", "декабря"
        }
    
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
        text_lower = text.lower()
        corrected_entities = entities.copy()
        
        if "WELL_NAME" in entities and "WELL_FIELD" in entities:
            well_name = entities["WELL_NAME"]
            well_field = entities["WELL_FIELD"]
            
            well_name_pos = text_lower.find(well_name.lower())
            well_field_pos = text_lower.find(well_field.lower())
            
            if well_name_pos != -1 and well_field_pos != -1:
                if well_field_pos < well_name_pos:
                    pass
                else:
                    if not self._is_valid_well_name(well_name):
                        corrected_entities["WELL_NAME"], corrected_entities["WELL_FIELD"] = \
                            corrected_entities["WELL_FIELD"], corrected_entities["WELL_NAME"]
        
        return corrected_entities
    
    def _is_valid_well_name(self, well_name: str) -> bool:
        if well_name.lower() in self.well_name_stop_words:
            return False
        
        if len(well_name) > 15:
            return False
        
        if not any(c.isdigit() for c in well_name):
            return False
        
        if well_name.lower() in {"две", "тысячи", "двадцать", "пятого"}:
            return False
        
        return True
    
    def extract_entities(self, ner_results: List[Dict[str, str]]) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        entities = {}
        raw_tokens = []
        current_entity = None
        current_tokens = []
        
        period_tokens = []
        
        for item in ner_results:
            token = item['token']
            tag = item['tag']
            
            raw_tokens.append({"token": token, "tag": tag})
            
            if 'PERIOD' in tag:
                period_tokens.append(token)
            
            if tag.startswith('B-'):
                if current_entity and current_tokens:
                    entity_type = current_entity.replace('B-', '').replace('I-', '')
                    entities[entity_type] = ' '.join(current_tokens)
                
                current_entity = tag
                current_tokens = [token]
                
            elif tag.startswith('I-') and current_entity:
                current_tokens.append(token)
                
            else:
                if current_entity and current_tokens:
                    entity_type = current_entity.replace('B-', '').replace('I-', '')
                    entities[entity_type] = ' '.join(current_tokens)
                    current_entity = None
                    current_tokens = []
        
        if current_entity and current_tokens:
            entity_type = current_entity.replace('B-', '').replace('I-', '')
            entities[entity_type] = ' '.join(current_tokens)
        
        if period_tokens and len(period_tokens) > 1:
            full_period = ' '.join(period_tokens)
            entities['PERIOD'] = full_period
            print(f"Combined PERIOD tokens: {full_period}")
        
        return entities, raw_tokens
    
    def parse_period_from_entities(self, entities: Dict[str, str]) -> Dict[str, str]:
        period_parts = []
        
        if "PERIOD" in entities:
            period_text = entities["PERIOD"]
            
            if "февраль" in period_text.lower() and "прошлого" in period_text.lower() and "года" in period_text.lower():
                print(f"Using full PERIOD: {period_text}")
                return date_parser.parse_period(period_text)
            
            if period_text == "года" and "прошлого" in str(entities):
                month = None
                for key, value in entities.items():
                    if value.lower() in self.month_words:
                        month = value
                        break
                
                if month:
                    full_period = f"{month} прошлого года"
                    print(f"Created full period from month + прошлого года: {full_period}")
                    return date_parser.parse_period(full_period)
                else:
                    period_parts.append("прошлого года")
            else:
                period_parts.append(period_text)
        
        if "MONTH" in entities:
            month = entities["MONTH"]
            month_lower = month.lower()
            if not any(month_lower in part.lower() for part in period_parts):
                period_parts.append(month)
        
        if "YEAR" in entities:
            year = entities["YEAR"]
            if year.isdigit() and len(year) == 4 and 1900 <= int(year) <= 2100:
                if not any(year in part for part in period_parts):
                    period_parts.append(year)
        
        if "DATE" in entities and entities["DATE"] not in " ".join(period_parts):
            period_parts.append(entities["DATE"])
        
        if period_parts:
            period_text = " ".join(period_parts)
            print(f"Parsing period from: '{period_text}'")
            return date_parser.parse_period(period_text)
        
        return {"start": "", "end": ""}
    
    def find_well_entities_by_rules(self, text: str) -> Dict[str, str]:
        entities = {}
        text_lower = text.lower()
        
        well_field = self.find_well_field_fast(text)
        if well_field:
            entities["WELL_FIELD"] = well_field
            print(f"Found well field by fast search: {well_field}")
        
        well_patterns = [
            (r'по\s+(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),
            (r'(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),
            (r'скв\.?\s*(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)', 1),
            (r'скважина\s*(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)', 1),
            (r'№\s*(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)', 1),
            (r'(\d+[А-Яа-я]?(?:/\d+)?[А-Яа-я]?)\s+(скважина|скв\.?)', (1, None)),
        ]
        
        for pattern, groups in well_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if isinstance(groups, tuple):
                    well_number = match.group(groups[0])
                    
                    if self._is_valid_well_name(well_number):
                        entities["WELL_NAME"] = well_number
                        
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
        
        if "WELL_NAME" not in entities:
            matches = re.findall(r'\b(\d+[А-Яа-я]?)\b', text)
            for match in matches:
                if len(match) == 4 and match.isdigit():
                    year = int(match)
                    if 1900 <= year <= 2100:
                        continue
                
                context_before = text_lower[:text_lower.find(match.lower())]
                if "за" in context_before or "в" in context_before:
                    context_after = text_lower[text_lower.find(match.lower()) + len(match):]
                    if any(month in context_after for month in ["январь", "февраль", "март"]):
                        continue
                
                entities["WELL_NAME"] = match
                break
        
        return entities
    
    def _check_well_field_candidate(self, candidate: str) -> Optional[str]:
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