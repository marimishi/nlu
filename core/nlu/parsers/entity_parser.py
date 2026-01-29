import re
from typing import Dict, Any, Optional, List, Tuple, Set
from collections import defaultdict

from core.nlu.parsers.date_parser import date_parser
from config.command_config import WELL_FIELDS, WELL_FIELDS_LOWER


class EntityParser:
    def __init__(self):
        self._init_search_structures()
    
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
        
        # Поиск по префиксам
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
                distance = abs(well_field_pos - (well_name_pos + len(well_name)))
                
                if distance < 3:
                    if any(c.isdigit() for c in well_name) and not any(c.isdigit() for c in well_field):
                        pass
                    else:
                        if well_field_pos < well_name_pos:
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
        
        # Не забываем последнюю сущность
        if current_entity and entity_tokens:
            entities[current_entity] = " ".join(entity_tokens)
        
        return entities, raw_tokens
    
    def parse_period_from_entities(self, entities: Dict[str, str]) -> Dict[str, str]:
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
            (r'по\s+(\d+[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),  # "по 850 покачевское"
            (r'(\d+[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),        # "850 покачевское"
            (r'скв\.?\s*(\d+[А-Яа-я]?)', 1),                 # "скв. 850"
            (r'скважина\s*(\d+[А-Яа-я]?)', 1),               # "скважина 123А"
            (r'№\s*(\d+[А-Яа-я]?)', 1),                      # "№ 45"
        ]
        
        for pattern, groups in well_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if isinstance(groups, tuple):
                    well_number = match.group(groups[0])
                    
                    if "WELL_FIELD" not in entities:
                        well_field_candidate = match.group(groups[1])
                        candidate_field = self._check_well_field_candidate(well_field_candidate)
                        if candidate_field:
                            entities["WELL_FIELD"] = candidate_field
                    
                    entities["WELL_NAME"] = well_number
                    return entities
                else:
                    well_number = match.group(groups)
                    entities["WELL_NAME"] = well_number
                    return entities
        
        if "WELL_NAME" not in entities:
            matches = re.findall(r'\b\d+[А-Яа-я]?\b', text)
            for match in matches:
                if not (len(match) == 4 and match.isdigit() and 1900 <= int(match) <= 2100):
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