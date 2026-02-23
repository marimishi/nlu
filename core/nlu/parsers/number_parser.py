import re
from typing import List, Tuple
from rus2num import Rus2Num


class NumberParser:
    
    def __init__(self):
        self.parser = Rus2Num()
        
    def convert_text_numbers_to_digits(self, text: str) -> str:
        if not text:
            return text
        
        words = text.split()
        result = []
        i = 0
        
        while i < len(words):
            if words[i].lower() == "дробь":
                result.append("/")
                i += 1
                continue
                
            if '/' in words[i]:
                result.append(words[i])
                i += 1
                continue
                
            if words[i].isdigit():
                result.append(words[i])
                i += 1
                continue
            
            number_words, consumed = self._extract_number_sequence(words, i)
            
            if number_words:
                number_text = " ".join(number_words)
                
                try:
                    parsed = self.parser(number_text)
                    
                    if parsed is not None and parsed != "":
                        parsed_str = str(parsed)
                        parsed_str = parsed_str.replace(" ", "")
                        result.append(parsed_str)
                        i += consumed
                        continue
                except Exception:
                    # Если парсинг не удался, просто пропускаем
                    pass
            
            result.append(words[i])
            i += 1
        
        return self._postprocess_result(" ".join(result))
    
    def _postprocess_result(self, text: str) -> str:
        words = text.split()
        result = []
        i = 0
        
        while i < len(words):
            if words[i].isdigit() or (words[i].replace('/', '').isdigit() and '/' in words[i]):
                number_parts = [words[i]]
                j = i + 1
                
                while j < len(words) and (words[j].isdigit() or words[j] == '/'):
                    number_parts.append(words[j])
                    j += 1
                
                combined = ''.join(number_parts)
                result.append(combined)
                i = j
            else:
                result.append(words[i])
                i += 1
        
        return ' '.join(result)
    
    def _extract_number_sequence(self, words: List[str], start: int) -> Tuple[List[str], int]:
        number_words = []
        i = start
        
        stop_words = {
            "год", "года", "лет", "месяц", "месяца", "дробь",
            "за", "на", "в", "с", "по", "от", "для", "к", "из",
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        }
        
        while i < len(words):
            word_lower = words[i].lower()
            
            if word_lower in stop_words:
                break
                
            if self._is_potential_number_word(word_lower):
                number_words.append(words[i])
            else:
                break
            i += 1
            
        return number_words, i - start
    
    def _is_potential_number_word(self, word: str) -> bool:
        number_words = {
            "ноль", "один", "одна", "одно", "два", "две", "три", "четыре",
            "пять", "шесть", "семь", "восемь", "девять",
            "десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать",
            "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать",
            "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят",
            "семьдесят", "восемьдесят", "девяносто",
            "сто", "двести", "триста", "четыреста", "пятьсот",
            "шестьсот", "семьсот", "восемьсот", "девятьсот",
            "тысяча", "тысячи", "тысяч",
            "миллион", "миллиона", "миллионов",
            "первого", "второго", "третьего", "четвертого", "пятого",
            "шестого", "седьмого", "восьмого", "девятого", "десятого",
            "одиннадцатого", "двенадцатого", "тринадцатого", "четырнадцатого",
            "пятнадцатого", "шестнадцатого", "семнадцатого", "восемнадцатого",
            "девятнадцатого", "двадцатого", "тридцатого", "сорокового",
            "пятидесятого", "шестидесятого", "семидесятого", "восьмидесятого",
            "девяностого", "сотого", "тысячного",
            
            "первое", "второе", "третье", "четвертое", "пятое",
            "шестое", "седьмое", "восьмое", "девятое", "десятое",
            "одиннадцатое", "двенадцатое", "тринадцатое", "четырнадцатое",
            "пятнадцатое", "шестнадцатое", "семнадцатое", "восемнадцатое",
            "девятнадцатое", "двадцатое", "тридцатое"
        }
        
        return word in number_words or word.isdigit()
