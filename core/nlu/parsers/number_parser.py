import re
from typing import Optional, Union, List, Tuple
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
        
        # Слова, которые указывают на конец числовой последовательности
        self.number_boundaries = {
            "за", "на", "в", "с", "по", "от", "для", "к", "из",
            "месяц", "месяца", "месяцев",
            "год", "года", "лет",
            "числа", "число"
        }
        
        # Слова, которые должны оставаться с годом
        self.year_suffixes = {"год", "года", "году", "годом", "г."}
        
        # Текущая дата для определения контекста
        self.current_date = datetime.now()
        self.current_year = self.current_date.year

    def convert_text_numbers_to_digits(self, text: str) -> str:
        """Преобразует текстовые числа в цифры с учетом контекста дат"""
        if not text:
            return text

        words = text.split()
        result = []
        i = 0
        
        while i < len(words):
            # Пропускаем обработку для дробей
            if '/' in words[i]:
                result.append(words[i])
                i += 1
                continue
            
            # Проверяем, не является ли слово уже числом
            if words[i].isdigit():
                result.append(words[i])
                i += 1
                continue
            
            # Специальная обработка для дат
            if self._is_date_context(words, i):
                date_result, consumed = self._process_date_number(words, i)
                result.extend(date_result)
                i += consumed
                continue
            
            # Обработка дробей из нескольких слов
            fraction_match = self._match_fraction(words, i)
            if fraction_match:
                parsed_fraction, consumed = fraction_match
                result.append(parsed_fraction)
                i += consumed
                continue
            
            # Обработка обычных чисел
            number_match = self._match_number(words, i)
            if number_match:
                parsed_number, consumed = number_match
                result.append(str(parsed_number))
                i += consumed
                continue
            
            result.append(words[i])
            i += 1
        
        return " ".join(result)
    
    def _is_date_context(self, words: List[str], start: int) -> bool:
        """Проверяет, находимся ли мы в контексте даты"""
        if start >= len(words):
            return False
        
        # Проверяем следующие слова на наличие месяцев или границ дат
        for i in range(start, min(start + 5, len(words))):
            word_lower = words[i].lower()
            if word_lower in self.months:
                return True
            if word_lower in {"год", "года", "г.", "лет"}:
                return True
        
        # Проверяем предыдущие слова
        for i in range(max(0, start - 3), start):
            word_lower = words[i].lower()
            if word_lower in {"за", "с", "по", "в", "на"} and i < start:
                # Проверим, что после предлога есть месяц
                for j in range(start, min(start + 3, len(words))):
                    if words[j].lower() in self.months:
                        return True
        
        return False
    
    def _process_date_number(self, words: List[str], start: int) -> Tuple[List[str], int]:
        """Обрабатывает числа в контексте дат, правильно определяя год"""
        number_words = []
        consumed = 0
        i = start
        
        # Собираем числовые слова
        while i < len(words):
            word_lower = words[i].lower()
            
            # Если встретили месяц, останавливаемся
            if word_lower in self.months:
                break
            
            # Если встретили границу, останавливаемся
            if word_lower in self.number_boundaries and word_lower not in self.year_suffixes:
                break
            
            if self._is_number_word(word_lower) or words[i].isdigit():
                number_words.append(words[i])
                i += 1
                consumed += 1
            else:
                break
        
        if not number_words:
            return [words[start]], 1
        
        # Парсим число
        number_text = " ".join(number_words).lower()
        print(f"Processing date number: '{number_text}'")
        parsed = self._parse_number_text(number_text)
        print(f"Parsed result: {parsed}")
        
        # Проверяем, является ли число вероятным годом
        is_likely_year = False
        if parsed is not None:
            # Годы обычно в диапазоне 1900-2100
            if 1900 <= parsed <= 2100:
                is_likely_year = True
                print(f"Number {parsed} is in year range 1900-2100")
            # Или если число большое (тысячи) - тоже вероятный год
            elif parsed >= 1000:
                is_likely_year = True
                print(f"Number {parsed} is >= 1000, treating as year")
        
        # Проверяем контекст для года
        if is_likely_year:
            # Это год, возвращаем просто число
            result = [str(parsed)]
            print(f"Returning year: {parsed}")
            
            # Проверяем, есть ли после числа "год" или "года"
            if i < len(words) and words[i].lower() in self.year_suffixes:
                print(f"Skipping year suffix: {words[i]}")
                consumed += 1  # Пропускаем слово "года"
        else:
            # Это не год, возвращаем как есть
            result = [str(parsed)] if parsed is not None else number_words
            print(f"Returning non-year number: {result}")
        
        return result, consumed

    def _match_number(self, words: List[str], start: int) -> Optional[tuple]:
        """Сопоставляет число из слов, начиная с позиции start"""
        if start >= len(words):
            return None
        
        number_words = []
        i = start
        
        while i < len(words):
            word_lower = words[i].lower()
            
            # Проверяем границы числа
            if word_lower in self.number_boundaries:
                break
            
            # Проверяем месяцы
            if word_lower in self.months:
                break
            
            # Проверяем годы в контексте
            if word_lower in self.year_suffixes and i > start:
                # Если предыдущее слово было числом, это год
                break
            
            if word_lower == "дробь":
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
        
        number_text = " ".join(number_words).lower()
        parsed = self._parse_number_text(number_text)
        
        if parsed is not None:
            return (parsed, len(number_words))
        
        return None

    def _match_fraction(self, words: List[str], start: int) -> Optional[tuple]:
        """Сопоставляет дробь вида 'сто двадцать три дробь один'"""
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
            
            if word_lower in self.number_boundaries:
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
        """Парсит текст числа в целое число"""
        words = text.split()
        if not words:
            return None
        
        print(f"Parsing number text: '{text}'")
        
        if len(words) == 1 and words[0].isdigit():
            return int(words[0])
        
        total = 0
        current = 0
        i = 0
        
        while i < len(words):
            word = words[i]
            word_norm = self._normalize_number_word(word)
            print(f"  Processing word: '{word}' (normalized: '{word_norm}')")
            
            # Обработка тысяч
            if word_norm in self.thousands:
                if current == 0:
                    current = 1
                total += current * 1000
                print(f"    Found thousand, total={total}, current={current}")
                current = 0
                i += 1
                continue
            
            # Обработка комбинаций типа "две тысячи"
            if i + 1 < len(words) and words[i+1] in self.thousands:
                num = self._parse_small_number(word)
                if num is not None:
                    total += num * 1000
                    print(f"    Found X thousand: {num}*1000, total={total}")
                    i += 2
                    continue
            
            # Обработка сотен, десятков, единиц
            num = self._parse_small_number(word)
            if num is not None:
                current += num
                print(f"    Added {num} to current, current={current}")
                i += 1
            else:
                remaining = " ".join(words[i:])
                try:
                    return int(remaining)
                except ValueError:
                    return None
        
        result = total + current if (total + current) > 0 else None
        print(f"Final parsed number: {result}")
        return result

    def _parse_small_number(self, word: str) -> Optional[int]:
        """Парсит маленькое число (до 999)"""
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
        """Нормализует слово числа (убирает окончания)"""
        word = word.lower()
        
        # Специальные случаи для числительных в родительном падеже
        # "двадцатого" -> "двадцать", "пятого" -> "пять" и т.д.
        special_cases = {
            "первого": "один",
            "второго": "два",
            "третьего": "три",
            "четвертого": "четыре",
            "пятого": "пять",
            "шестого": "шесть",
            "седьмого": "семь",
            "восьмого": "восемь",
            "девятого": "девять",
            "десятого": "десять",
            "одиннадцатого": "одиннадцать",
            "двенадцатого": "двенадцать",
            "тринадцатого": "тринадцать",
            "четырнадцатого": "четырнадцать",
            "пятнадцатого": "пятнадцать",
            "шестнадцатого": "шестнадцать",
            "семнадцатого": "семнадцать",
            "восемнадцатого": "восемнадцать",
            "девятнадцатого": "девятнадцать",
            "двадцатого": "двадцать",
            "тридцатого": "тридцать",
            "сотого": "сто",
            "тысячного": "тысяча"
        }
        
        if word in special_cases:
            return special_cases[word]
        
        # Для составных числительных типа "двадцать пятого"
        if "двадцать" in word and "пятого" in word:
            return "двадцать пять"
        if "двадцать" in word and "шестого" in word:
            return "двадцать шесть"
        if "двадцать" in word and "седьмого" in word:
            return "двадцать семь"
        if "двадцать" in word and "восьмого" in word:
            return "двадцать восемь"
        if "двадцать" in word and "девятого" in word:
            return "двадцать девять"
        if "тридцать" in word and "первого" in word:
            return "тридцать один"
        
        # Стандартные окончания
        endings = ['ого', 'ому', 'ым', 'ом', 'ая', 'яя', 'ое', 'ее', 'ые', 'ие',
                   'ой', 'ей', 'ую', 'юю', 'ых', 'их', 'ыми', 'ими']
        
        for ending in endings:
            if word.endswith(ending):
                base = word[:-len(ending)]
                # Проверяем особые случаи
                if base in self.digits or base in self.teens or base in self.tens or base in self.hundreds:
                    return base
                return word[:-len(ending)]
        
        if word.endswith('ая') or word.endswith('яя'):
            base = word[:-2] + 'а'
            return base
        if word.endswith('ое') or word.endswith('ее'):
            base = word[:-2] + 'о'
            return base
        if word.endswith('ые') or word.endswith('ие'):
            base = word[:-2] + 'ы'
            return base
        
        return word

    def _is_number_word(self, word: str) -> bool:
        """Проверяет, является ли слово числительным"""
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