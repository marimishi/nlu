import re
from typing import Optional, Union, List


class NumberParser:
    def __init__(self):
        self.digits = {
            "ноль": 0, "один": 1, "одна": 1, "два": 2, "две": 2,
            "три": 3, "четыре": 4, "пять": 5, "шесть": 6,
            "семь": 7, "восемь": 8, "девять": 9
        }

        self.teens = {
            "десять": 10, "одиннадцать": 11, "двенадцать": 12,
            "тринадцать": 13, "четырнадцать": 14, "пятнадцать": 15,
            "шестнадцать": 16, "семнадцать": 17, "восемнадцать": 18,
            "девятнадцать": 19
        }

        self.tens = {
            "двадцать": 20, "тридцать": 30, "сорок": 40,
            "пятьдесят": 50, "шестьдесят": 60, "семьдесят": 70,
            "восемьдесят": 80, "девяносто": 90
        }

        self.hundreds = {
            "сто": 100, "двести": 200, "триста": 300,
            "четыреста": 400, "пятьсот": 500, "шестьсот": 600,
            "семьсот": 700, "восемьсот": 800, "девятьсот": 900
        }

        self.thousands = {
            "тысяча": 1000, "тысячи": 1000, "тысяч": 1000
        }

        self.months = {
            "январь", "февраль", "март", "апрель", "май", "июнь",
            "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        }

    def convert_text_numbers_to_digits(self, text: str) -> str:
        if not text:
            return text

        words = text.split()
        result = []
        i = 0
        
        while i < len(words):
            if '/' in words[i]:
                result.append(words[i])
                i += 1
                continue
            
            fraction_match = self._match_fraction(words, i)
            if fraction_match:
                parsed_fraction, consumed = fraction_match
                result.append(parsed_fraction)
                i += consumed
                continue
            
            number_match = self._match_number(words, i)
            if number_match:
                parsed_number, consumed = number_match
                result.append(str(parsed_number))
                i += consumed
                continue
            
            result.append(words[i])
            i += 1
        
        return " ".join(result)

    def _match_number(self, words: List[str], start: int) -> Optional[tuple]:
        if start >= len(words):
            return None
        
        number_words = []
        i = start
        
        while i < len(words):
            word_lower = words[i].lower()
            
            if word_lower in self.months:
                break
            
            if word_lower == "дробь":
                break
            
            if word_lower in {"за", "на", "в", "с", "по", "от", "для", "к", "из"}:
                break
            
            if word_lower.isdigit():
                number_words.append(words[i])
                i += 1
                continue
            
            if self._is_number_word(word_lower):
                number_words.append(words[i])
                i += 1
                continue
            
            break
        
        if not number_words:
            return None
        
        number_text = " ".join(number_words)
        parsed = self._parse_number_text(number_text.lower())
        
        if parsed is not None:
            return (parsed, len(number_words))
        
        return None

    def _match_fraction(self, words: List[str], start: int) -> Optional[tuple]:
        if start + 2 >= len(words):
            return None
        
        fraction_idx = None
        for i in range(start, min(start + 5, len(words))):
            if words[i].lower() == "дробь":
                fraction_idx = i
                break
        
        if fraction_idx is None:
            return None
        
        numerator_words = []
        for j in range(start, fraction_idx):
            if not self._is_number_word(words[j].lower()) and not words[j].isdigit():
                return None
            numerator_words.append(words[j])
        
        denominator_words = []
        k = fraction_idx + 1
        while k < len(words):
            word_lower = words[k].lower()
            
            if word_lower in self.months:
                break
            
            if word_lower in {"за", "на", "в", "с", "по", "от", "для", "к", "из"}:
                break
            
            if not self._is_number_word(word_lower) and not words[k].isdigit():
                break
            
            denominator_words.append(words[k])
            k += 1
        
        if not numerator_words or not denominator_words:
            return None
        
        numerator_text = " ".join(numerator_words)
        denominator_text = " ".join(denominator_words)
        
        numerator = self._parse_number_text(numerator_text.lower())
        if numerator is None:
            try:
                numerator = int(numerator_text)
            except ValueError:
                return None
        
        denominator = self._parse_number_text(denominator_text.lower())
        if denominator is None:
            try:
                denominator = int(denominator_text)
            except ValueError:
                return None
        
        fraction = f"{numerator}/{denominator}"
        return (fraction, len(numerator_words) + 1 + len(denominator_words))

    def _parse_number_text(self, text: str) -> Optional[int]:
        words = text.split()
        if not words:
            return None
        
        if len(words) == 1 and words[0].isdigit():
            return int(words[0])
        
        total = 0
        current = 0
        i = 0
        
        while i < len(words):
            word = words[i]
            word_norm = self._normalize_number_word(word)
            
            if word_norm in self.thousands:
                if current == 0:
                    current = 1
                total += current * 1000
                current = 0
                i += 1
                continue
            
            if i + 1 < len(words) and words[i+1] in self.thousands:
                num = self._parse_small_number(word)
                if num is not None:
                    total += num * 1000
                    i += 2
                    continue
            
            num = self._parse_small_number(word)
            if num is not None:
                current += num
                i += 1
            else:
                remaining = " ".join(words[i:])
                try:
                    return int(remaining)
                except ValueError:
                    return None
        
        return total + current if (total + current) > 0 else None

    def _parse_small_number(self, word: str) -> Optional[int]:
        word_norm = self._normalize_number_word(word)
        
        if word_norm in self.digits:
            return self.digits[word_norm]
        elif word_norm in self.teens:
            return self.teens[word_norm]
        elif word_norm in self.tens:
            return self.tens[word_norm]
        elif word_norm in self.hundreds:
            return self.hundreds[word_norm]
        elif word.isdigit():
            return int(word)
        
        return None

    def _normalize_number_word(self, word: str) -> str:
        word = word.lower()
        
        endings = ['ого', 'ому', 'ым', 'ом', 'ая', 'яя', 'ое', 'ее', 'ые', 'ие',
                   'ой', 'ей', 'ую', 'юю', 'ых', 'их', 'ыми', 'ими']
        
        for ending in endings:
            if word.endswith(ending):
                return word[:-len(ending)]
        
        if word.endswith('ая') or word.endswith('яя'):
            return word[:-2] + 'а'
        if word.endswith('ое') or word.endswith('ее'):
            return word[:-2] + 'о'
        if word.endswith('ые') or word.endswith('ие'):
            return word[:-2] + 'ы'
        
        return word

    def _is_number_word(self, word: str) -> bool:
        word = word.lower()
        word_norm = self._normalize_number_word(word)
        
        return (
            word in self.digits
            or word in self.teens
            or word in self.tens
            or word in self.hundreds
            or word in self.thousands
            or word_norm in self.digits
            or word_norm in self.teens
            or word_norm in self.tens
            or word_norm in self.hundreds
            or word_norm in self.thousands
            or word.isdigit()
            or word == "дробь"
        )


number_parser = NumberParser()