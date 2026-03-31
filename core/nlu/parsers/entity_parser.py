import re
from typing import Dict, Any, List, Tuple, Set, Optional
from collections import defaultdict

from ...nlu.parsers.date_parser import date_parser
from ....config.command_config import WELL_FIELDS, WELL_FIELDS_LOWER


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
        
        self.well_name_pattern = re.compile(
            r'^(\d+[А-Яа-я]?|\d+/\d+[А-Яа-я]?|\d+[-\s]?[А-Яа-я])$'
        )
        
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
        
        # Паттерны для определения месторождений по контексту
        self.field_context_patterns = [
            (r'(?:на|по|в|с|со|к|от|до|из)\s+([А-Яа-яё][а-яё]+(?:[-\s][А-Яа-яё]+)?)(?:\s+(?:месторождени[еяю]|площад[иь]))?', 1),
            (r'(?:месторождени[еяю]|площад[иь])\s+([А-Яа-яё][а-яё]+(?:[-\s][А-Яа-яё]+)?)', 1),
            (r'([А-Яа-яё][а-яё]+(?:[-\s][А-Яа-яё]+)?)\s+(?:месторождени[еяю]|площад[иь])', 1),
            (r'([А-Яа-яё][а-яё]*(?:овск|евск|инск|енск|уртск)[а-яё]*)(?:\s+(?:месторождени[еяю]|площад[иь]))?', 1),
        ]
        
        self.not_field_markers = {
            "год", "года", "месяц", "январь", "февраль", "март", "апрель",
            "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь",
            "декабрь", "тысячи", "двадцать", "тридцать", "сорок", "пятьдесят",
            "скважина", "скв", "куст", "добыча", "дебит", "обводненность"
        }
        
        self.field_stop_words = {
            "прошлый", "прошлого", "текущий", "текущего", "следующий",
            "следующего", "последний", "последнего", "первый", "первого",
            "второй", "второго", "третий", "третьего", "весь", "всего",
            "целый", "целого", "новый", "нового", "старый", "старого"
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
    
    def _save_entity(self, entities: Dict[str, str], entity_type: str, tokens: List[str], well_field_tokens: List[str] = None):
        if well_field_tokens is None:
            well_field_tokens = []
            
        if entity_type == 'WELL_FIELD':
            if well_field_tokens:
                combined = ' '.join(well_field_tokens)
                entities[entity_type] = combined
                print(f"Saved WELL_FIELD: '{combined}' from tokens: {well_field_tokens}")
            else:
                combined = ' '.join(tokens)
                entities[entity_type] = combined
        else:
            combined = ' '.join(tokens)
            entities[entity_type] = combined
    
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
    
    def find_field_by_context(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        
        for pattern, group_num in self.field_context_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                candidate = match.group(group_num).strip()
                
                if len(candidate) < 3:
                    continue
                
                if candidate in self.field_stop_words:
                    continue
                
                if candidate in self.not_field_markers:
                    continue
                
                if candidate.isdigit() or (candidate.replace('-', '').isdigit()):
                    continue
                
                if candidate in self.month_words:
                    continue
                
                print(f"Found field by context: '{candidate}'")
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
        
        if len(well_name) > 20:
            return False
        
        if not any(c.isdigit() for c in well_name):
            return False
        
        if well_name.lower() in {"две", "тысячи", "двадцать", "пятого"}:
            return False
        
        if ' ' in well_name:
            parts = well_name.split()
            if len(parts) == 2:
                if parts[0].isdigit() and parts[1].isalpha() and len(parts[1]) == 1:
                    return True
        
        return True
    
    def extract_entities(self, ner_results: List[Dict[str, str]]) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        entities = {}
        raw_tokens = []
        current_entity = None
        current_tokens = []
        
        period_tokens = []
        year_tokens = []
        month_tokens = []
        
        well_name_tokens = []
        well_field_tokens = []
        
        for i, item in enumerate(ner_results):
            token = item['token']
            tag = item['tag']
            
            raw_tokens.append({"token": token, "tag": tag})
            
            # Собираем все PERIOD токены
            if 'PERIOD' in tag:
                period_tokens.append(token)
            
            # Собираем YEAR токены отдельно
            if 'YEAR' in tag:
                year_tokens.append(token)
            
            # Собираем MONTH токены
            if 'MONTH' in tag:
                month_tokens.append(token)
            
            # Обработка WELL_FIELD токенов
            if 'WELL_FIELD' in tag:
                if tag.startswith('B-'):
                    if current_entity and current_tokens:
                        entity_type = current_entity.replace('B-', '').replace('I-', '')
                        self._save_entity(entities, entity_type, current_tokens, well_field_tokens)
                    
                    current_entity = tag
                    current_tokens = [token]
                    well_field_tokens = [token]
                elif tag.startswith('I-') and current_entity and 'WELL_FIELD' in current_entity:
                    current_tokens.append(token)
                    well_field_tokens.append(token)
                else:
                    if current_entity and current_tokens:
                        entity_type = current_entity.replace('B-', '').replace('I-', '')
                        self._save_entity(entities, entity_type, current_tokens, well_field_tokens)
                    
                    current_entity = tag
                    current_tokens = [token]
                    if 'WELL_FIELD' in tag:
                        well_field_tokens = [token]
            
            # Обработка WELL_NAME токенов
            elif 'WELL_NAME' in tag:
                if tag.startswith('B-'):
                    if current_entity and current_tokens:
                        entity_type = current_entity.replace('B-', '').replace('I-', '')
                        self._save_entity(entities, entity_type, current_tokens, well_field_tokens)
                    
                    current_entity = tag
                    current_tokens = [token]
                    well_name_tokens = [token]
                elif tag.startswith('I-') and current_entity and 'WELL_NAME' in current_entity:
                    current_tokens.append(token)
                    well_name_tokens.append(token)
                else:
                    if current_entity and current_tokens:
                        entity_type = current_entity.replace('B-', '').replace('I-', '')
                        self._save_entity(entities, entity_type, current_tokens, well_field_tokens)
                    
                    current_entity = tag
                    current_tokens = [token]
                    if 'WELL_NAME' in tag:
                        well_name_tokens = [token]
            
            elif tag.startswith('B-'):
                if current_entity and current_tokens:
                    entity_type = current_entity.replace('B-', '').replace('I-', '')
                    self._save_entity(entities, entity_type, current_tokens, well_field_tokens)
                
                current_entity = tag
                current_tokens = [token]
                well_field_tokens = []
                well_name_tokens = []
                
            elif tag.startswith('I-') and current_entity:
                current_tokens.append(token)
                if 'WELL_FIELD' in current_entity:
                    well_field_tokens.append(token)
                elif 'WELL_NAME' in current_entity:
                    well_name_tokens.append(token)
                
            else:
                if current_entity and current_tokens:
                    entity_type = current_entity.replace('B-', '').replace('I-', '')
                    self._save_entity(entities, entity_type, current_tokens, well_field_tokens)
                    current_entity = None
                    current_tokens = []
                    well_field_tokens = []
                    well_name_tokens = []
        
        if current_entity and current_tokens:
            entity_type = current_entity.replace('B-', '').replace('I-', '')
            self._save_entity(entities, entity_type, current_tokens, well_field_tokens)
        
        # Объединяем несколько WELL_FIELD токенов
        well_fields = []
        for token_info in raw_tokens:
            if 'WELL_FIELD' in token_info['tag']:
                well_fields.append(token_info['token'])
        
        if len(well_fields) > 1:
            combined_well_field = ' '.join(well_fields)
            entities['WELL_FIELD'] = combined_well_field
            print(f"Combined multiple WELL_FIELD tokens: '{combined_well_field}'")
        
        # Объединяем WELL_NAME токены
        if "WELL_NAME" in entities:
            all_well_names = []
            in_well_name = False
            for token_info in raw_tokens:
                if 'WELL_NAME' in token_info['tag']:
                    if token_info['tag'].startswith('B-'):
                        if in_well_name:
                            all_well_names.append(' ')
                        all_well_names.append(token_info['token'])
                        in_well_name = True
                    else:
                        if in_well_name:
                            all_well_names.append(' ')
                        all_well_names.append(token_info['token'])
                        in_well_name = True
                else:
                    if in_well_name:
                        in_well_name = False
            
            if all_well_names:
                combined_well_name = ''.join(all_well_names)
                if combined_well_name != entities["WELL_NAME"]:
                    print(f"Combining WELL_NAME tokens: '{combined_well_name}'")
                    entities["WELL_NAME"] = combined_well_name
        
        # Объединяем PERIOD токены
        if period_tokens:
            full_period = ' '.join(period_tokens)
            entities['PERIOD'] = full_period
            print(f"Combined PERIOD tokens: {full_period}")
        
        # Объединяем YEAR токены и добавляем в PERIOD если нужно
        if year_tokens:
            year_value = ' '.join(year_tokens)
            # Если YEAR это не просто слово "года", а реальное число
            if year_value.isdigit() or (year_value.replace(' ', '').isdigit()):
                if 'PERIOD' in entities:
                    # Добавляем год к периоду
                    entities['PERIOD'] = f"{entities['PERIOD']} {year_value}"
                else:
                    entities['PERIOD'] = year_value
                print(f"Added year to PERIOD: {year_value}")
            else:
                # Если YEAR это "года", но есть отдельный год в другом месте
                # Ищем цифровой год в raw_tokens
                for token_info in raw_tokens:
                    if token_info['token'].isdigit() and len(token_info['token']) == 4:
                        if 'PERIOD' in entities:
                            entities['PERIOD'] = f"{entities['PERIOD']} {token_info['token']}"
                        else:
                            entities['PERIOD'] = token_info['token']
                        print(f"Found digit year and added to PERIOD: {token_info['token']}")
                        break
        
        # Объединяем MONTH токены
        if month_tokens:
            month_value = ' '.join(month_tokens)
            if 'PERIOD' in entities:
                # Если месяц еще не в PERIOD
                if month_value not in entities['PERIOD']:
                    entities['PERIOD'] = f"{month_value} {entities['PERIOD']}"
            else:
                entities['PERIOD'] = month_value
            print(f"Added month to PERIOD: {month_value}")
        
        return entities, raw_tokens

    def parse_period_from_entities(self, entities: Dict[str, str]) -> Dict[str, str]:
        period_parts = []
        
        # Собираем полный период из всех частей
        if "PERIOD" in entities:
            period_parts.append(entities["PERIOD"])
        
        if "YEAR" in entities and entities["YEAR"] not in " ".join(period_parts):
            year_val = entities["YEAR"]
            # Если YEAR это "года", не добавляем его отдельно
            if year_val not in ["года", "год"]:
                period_parts.append(year_val)
        
        if "MONTH" in entities:
            month = entities["MONTH"]
            if not any(month in part for part in period_parts):
                period_parts.append(month)
        
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
        
        field_by_context = self.find_field_by_context(text)
        if field_by_context:
            entities["WELL_FIELD"] = field_by_context
            print(f"Found well field by context: {field_by_context}")
        else:
            well_field = self.find_well_field_fast(text)
            if well_field:
                entities["WELL_FIELD"] = well_field
                print(f"Found well field by fast search: {well_field}")
        
        well_patterns = [
            (r'по\s+(\d+)\s+([А-Яа-я])\s+([а-яё\-]+)', (1, 3, 2)),
            (r'(\d+)\s+([А-Яа-я])\s+([а-яё\-]+)', (1, 3, 2)),
            (r'по\s+(\d+[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),
            (r'(\d+[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),
            (r'по\s+(\d+/\d+[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),
            (r'(\d+/\d+[А-Яа-я]?)\s+([а-яё\-]+)', (1, 2)),
            (r'скв\.?\s*(\d+(?:\s+[А-Яа-я])?(?:/\d+)?[А-Яа-я]?)', 1),
            (r'скважина\s*(\d+(?:\s+[А-Яа-я])?(?:/\d+)?[А-Яа-я]?)', 1),
            (r'№\s*(\d+(?:\s+[А-Яа-я])?(?:/\d+)?[А-Яа-я]?)', 1),
            (r'(\d+(?:\s+[А-Яа-я])?(?:/\d+)?[А-Яа-я]?)\s+(скважина|скв\.?)', (1, None)),
        ]
        
        for pattern, groups in well_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if isinstance(groups, tuple):
                    if len(groups) == 3:
                        well_number = match.group(groups[0])
                        letter = match.group(groups[2])
                        well_name = f"{well_number} {letter}".strip()
                        
                        if self._is_valid_well_name(well_name):
                            entities["WELL_NAME"] = well_name
                            
                            if groups[1] is not None and "WELL_FIELD" not in entities:
                                well_field_candidate = match.group(groups[1])
                                candidate_field = self._check_well_field_candidate(well_field_candidate)
                                if candidate_field:
                                    entities["WELL_FIELD"] = candidate_field
                            
                            return entities
                    else:
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
            compound_matches = re.findall(r'\b(\d+)\s+([А-Яа-я])\b', text)
            for match in compound_matches:
                number, letter = match
                well_name = f"{number} {letter}"
                entities["WELL_NAME"] = well_name
                break
            
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