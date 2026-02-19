import re
from typing import Optional, List, Tuple
from datetime import datetime

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

        self.number_boundaries = {
            "за", "на", "в", "с", "по", "от", "для", "к", "из",
            "месяц", "месяца", "месяцев",
            "год", "года", "лет",
            "числа", "число"
        }

        self.year_suffixes = {"год", "года", "году", "годом", "г."}

        self.current_date = datetime.now()
        self.current_year = self.current_date.year

    def convert_text_numbers_to_digits(self, text: str) -> str:
        if not text:
            return text

        words = text.split()
        result = []
        i = 0

        while i < len(words):
            word = words[i]

            if '/' in word:
                result.append(word)
                i += 1
                continue

            if word.isdigit():
                result.append(word)
                i += 1
                continue

            if self._is_date_context(words, i):
                date_result, consumed = self._process_date_number(words, i)
                result.extend(date_result)
                i += consumed
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

            result.append(word)
            i += 1

        return " ".join(result)

    def _is_date_context(self, words: List[str], start: int) -> bool:
        for i in range(start, min(start + 5, len(words))):
            if words[i].lower() in self.months or words[i].lower() in {"год", "года", "г.", "лет"}:
                return True
        for i in range(max(0, start - 3), start):
            if words[i].lower() in {"за", "с", "по", "в", "на"}:
                for j in range(start, min(start + 3, len(words))):
                    if words[j].lower() in self.months:
                        return True
        return False

    def _process_date_number(self, words: List[str], start: int) -> Tuple[List[str], int]:
        number_words = []
        consumed = 0
        i = start
        while i < len(words):
            word_lower = words[i].lower()
            if word_lower in self.months or (word_lower in self.number_boundaries and word_lower not in self.year_suffixes):
                break
            if self._is_number_word(word_lower) or words[i].isdigit():
                number_words.append(words[i])
                consumed += 1
            else:
                break
            i += 1

        if not number_words:
            return [words[start]], 1

        number_text = " ".join(number_words).lower()
        parsed = self._parse_number_text(number_text)
        return [str(parsed)] if parsed is not None else number_words, consumed

    def _match_number(self, words: List[str], start: int) -> Optional[Tuple[int, int]]:
        number_words = []
        i = start
        while i < len(words):
            word_lower = words[i].lower()
            if word_lower in self.number_boundaries or word_lower in self.months or (word_lower in self.year_suffixes and i > start) or word_lower == "дробь":
                break
            if self._is_number_word(word_lower) or words[i].isdigit():
                number_words.append(words[i])
            else:
                break
            i += 1
        if not number_words:
            return None
        number_text = " ".join(number_words).lower()
        parsed = self._parse_number_text(number_text)
        if parsed is not None:
            return parsed, len(number_words)
        return None

    def _match_fraction(self, words: List[str], start: int) -> Optional[Tuple[str, int]]:
        if start + 2 >= len(words):
            return None
        fraction_idx = None
        for i in range(start, min(start + 5, len(words))):
            if words[i].lower() == "дробь":
                fraction_idx = i
                break
        if fraction_idx is None:
            return None
        numerator_words = words[start:fraction_idx]
        denominator_words = []
        k = fraction_idx + 1
        while k < len(words):
            word_lower = words[k].lower()
            if word_lower in self.months or word_lower in self.number_boundaries:
                break
            if not self._is_number_word(word_lower) and not words[k].isdigit():
                break
            denominator_words.append(words[k])
            k += 1
        if not numerator_words or not denominator_words:
            return None
        numerator = self._parse_number_text(" ".join(numerator_words))
        denominator = self._parse_number_text(" ".join(denominator_words))
        if numerator is None or denominator is None:
            return None
        return f"{numerator}/{denominator}", len(numerator_words) + 1 + len(denominator_words)

    def _parse_number_text(self, text: str) -> Optional[int]:
        words = text.split()
        if not words:
            return None
        if len(words) == 1 and words[0].isdigit():
            return int(words[0])

        values = []
        for word in words:
            val = self._parse_small_number(word)
            if val is None:
                return None
            values.append(val)
        
        return self._build_number(values)
    
    def _build_number(self, values: List[int]) -> int:
        if not values:
            return 0
        
        if len(values) == 2 and values[0] < 100 and values[1] >= 100:
            return values[0] * 1000 + values[1]
        
        if len(values) == 3 and values[0] >= 20 and values[1] < 10 and values[2] < 10:
            return (values[0] + values[1]) * 10 + values[2]
        
        if 0 in values:
            return self._build_with_zero(values)
        
        result = 0
        current = 0
        
        for val in values:
            if val >= 1000:
                if current == 0:
                    current = 1
                result += current * val
                current = 0
            elif val >= 100:
                if current != 0:
                    result += current
                current = val
            else:
                if current >= 100:
                    result += current
                    current = val
                elif current >= 10 and val < 10:
                    current += val
                else:
                    if current != 0:
                        result += current
                    current = val
        
        if current != 0:
            result += current
        
        return result
    
    def _build_with_zero(self, values: List[int]) -> int:
        zero_pos = -1
        for i, val in enumerate(values):
            if val == 0:
                zero_pos = i
                break
        
        if zero_pos == -1:
            result = 0
            for val in values:
                result = result * 10 + val
            return result
        
        left_values = values[:zero_pos]
        right_values = values[zero_pos + 1:]
        
        left_num = 0
        for val in left_values:
            left_num = left_num * 10 + val
        
        right_num = 0
        for val in right_values:
            if val >= 10:
                if right_num == 0:
                    right_num = val
                else:
                    if val < 10:
                        right_num = right_num * 10 + val
                    else:
                        right_num = right_num + val
            else:
                if right_num == 0:
                    right_num = val
                else:
                    right_num = right_num * 10 + val
        
        if len(left_values) == 0:
            return right_num
        elif left_values[-1] >= 100:
            return left_num + right_num
        elif left_values[-1] >= 10:
            if right_num < 10:
                return left_num * 10 + right_num
            elif right_num < 100:
                return left_num * 1000 + right_num
            else:
                return left_num * (10 ** len(str(right_num))) + right_num
        else:
            if right_num < 10:
                return left_num * 10 + right_num
            elif right_num < 100:
                return left_num * 100 + right_num
            else:
                return left_num * (10 ** len(str(right_num))) + right_num

    def _parse_small_number(self, word: str) -> Optional[int]:
        word_norm = self._normalize_number_word(word)
        if word_norm in self.digits:
            return self.digits[word_norm]
        if word_norm in self.teens:
            return self.teens[word_norm]
        if word_norm in self.tens:
            return self.tens[word_norm]
        if word_norm in self.hundreds:
            return self.hundreds[word_norm]
        if word_norm in self.thousands:
            return self.thousands[word_norm]
        if word.isdigit():
            return int(word)
        return None

    def _normalize_number_word(self, word: str) -> str:
        word = word.lower()
        special_cases = {
            "первого": "один", "второго": "два", "третьего": "три",
            "четвертого": "четыре", "пятого": "пять", "шестого": "шесть",
            "седьмого": "семь", "восьмого": "восемь", "девятого": "девять",
            "десятого": "десять", "одиннадцатого": "одиннадцать", "двенадцатого": "двенадцать",
            "тринадцатого": "тринадцать", "четырнадцатого": "четырнадцать", "пятнадцатого": "пятнадцать",
            "шестнадцатого": "шестнадцать", "семнадцатого": "семнадцать", "восемнадцатого": "восемнадцать",
            "девятнадцатого": "девятнадцать", "двадцатого": "двадцать",
            "тридцатого": "тридцать", "сорокового": "сорок", "пятидесятого": "пятьдесят",
            "шестидесятого": "шестьдесят", "семидесятого": "семьдесят", "восьмидесятого": "восемьдесят",
            "девяностого": "девяносто", "сотого": "сто", "тысячного": "тысяча"
        }
        return special_cases.get(word, word)

    def _is_number_word(self, word: str) -> bool:
        word = word.lower()
        word_norm = self._normalize_number_word(word)
        return (
            word in self.digits or word in self.teens or word in self.tens or
            word in self.hundreds or word in self.thousands or
            word_norm in self.digits or word_norm in self.teens or
            word_norm in self.tens or word_norm in self.hundreds or word_norm in self.thousands or
            word.isdigit() or word == "дробь"
        )

number_parser = NumberParser()

if __name__ == "__main__":
    test_cases = [
        ("двадцать три один", "231"),
        ("восемьдесят сто", "80100"),
        ("сто двадцать три", "123"),
        ("сто два", "102"),
        ("пятьсот сорок два", "542"),
        ("тысяча двести", "1200"),
        ("две тысячи двадцать пятого", "2025"),
        ("сто двадцать три дробь один", "123/1"),
        ("двадцать ноль восемьдесят шесть", "20086"),
        ("пятьсот ноль три", "503"),
        ("тысяча ноль двадцать пять", "1025"),
    ]
    
    for input_text, expected in test_cases:
        result = number_parser.convert_text_numbers_to_digits(input_text)
        print(f"'{input_text}': '{result}' (ожидалось '{expected}')")
        if result != expected:
            print(f"  Ошибка")
        else:
            print(f"  Успех")
    
    print("\nВсе тесты завершены!")