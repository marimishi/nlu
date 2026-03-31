import re
from typing import Optional, Dict, Any


def normalize_well_field(well_field: Optional[str]) -> Optional[str]:
    """
    Простой нормализатор для названия месторождения.
    Заменяет окончания: ий, ая, ой, ому, ый на "ое".
    
    Args:
        well_field: Название месторождения для нормализации
        
    Returns:
        Нормализованное название или оригинал
    """
    if not well_field or not isinstance(well_field, str):
        return well_field
    
    if ' ' in well_field.strip():
        return well_field
    
    word = well_field.strip()
    word_lower = word.lower()
    
    endings_to_replace = ['ого', 'его', 'ому', 'ему', 'ым', 'им', 'ом', 'ем', 'ыми', 'ими', 'ой', 'ей', 'ые', 'ие', 'ых', 'их', 'ий', 'ый', 'ой', 'ая', 'яя', 'ое', 'ее', 'ии', 'ыи', 'ия', 'ья']
    
    for ending in endings_to_replace:
        if word_lower.endswith(ending):
            base = word[:-len(ending)]
            normalized = base + 'ое'
            
            if word[0].isupper():
                normalized = normalized[0].upper() + normalized[1:]
            
            print(f"Нормализация well_field: '{word}' -> '{normalized}'")
            return normalized
    
    return word