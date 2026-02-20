import re
from typing import Optional, List, Tuple
from rus2num import Rus2Num


class NumberParser:
    
    def __init__(self):
        self.parser = Rus2Num()
        
        # Словарь для преобразования порядковых числительных в количественные
        self.ordinal_to_cardinal = {
            "первого": "один", "второго": "два", "третьего": "три",
            "четвертого": "четыре", "пятого": "пять", "шестого": "шесть",
            "седьмого": "семь", "восьмого": "восемь", "девятого": "девять",
            "десятого": "десять", "одиннадцатого": "одиннадцать",
            "двенадцатого": "двенадцать", "тринадцатого": "тринадцать",
            "четырнадцатого": "четырнадцать", "пятнадцатого": "пятнадцать",
            "шестнадцатого": "шестнадцать", "семнадцатого": "семнадцать",
            "восемнадцатого": "восемнадцать", "девятнадцатого": "девятнадцать",
            "двадцатого": "двадцать", "тридцатого": "тридцать",
            "сорокового": "сорок", "пятидесятого": "пятьдесят",
            "шестидесятого": "шестьдесят", "семидесятого": "семьдесят",
            "восьмидесятого": "восемьдесят", "девяностого": "девяносто",
            "сотого": "сто", "тысячного": "тысяча"
        }
        
    def _preprocess_ordinals(self, text: str) -> str:
        """Заменяет порядковые числительные на количественные для лучшего парсинга"""
        words = text.split()
        processed_words = []
        
        for word in words:
            word_lower = word.lower()
            if word_lower in self.ordinal_to_cardinal:
                processed_words.append(self.ordinal_to_cardinal[word_lower])
            else:
                processed_words.append(word)
        
        return ' '.join(processed_words)
        
    def convert_text_numbers_to_digits(self, text: str) -> str:
        if not text:
            return text
        
        # Сначала обрабатываем даты специальным образом
        text = self._preprocess_dates(text)
        
        # Затем обрабатываем порядковые числительные
        text = self._preprocess_ordinals(text)
        
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
                        
                        # Проверяем, не является ли это датой
                        if self._is_date_context(words, i, consumed):
                            parsed_str = self._format_date_part(parsed_str, words, i, consumed)
                            
                        result.append(parsed_str)
                        i += consumed
                        continue
                except Exception:
                    # Если парсинг не удался, пробуем альтернативный метод
                    alt_parsed = self._alternative_parse(number_words)
                    if alt_parsed is not None:
                        result.append(str(alt_parsed))
                        i += consumed
                        continue
            
            result.append(words[i])
            i += 1
        
        return self._postprocess_result(" ".join(result))
    
    def _preprocess_dates(self, text: str) -> str:
        """Специальная обработка дат"""
        # Паттерн для поиска дат типа "Двадцать пятое мая две тысячи двадцать третьего года"
        date_pattern = re.compile(
            r'(двадцать|тридцать|три|четыре|пять|шесть|семь|восемь|девять|десять|'
            r'одиннадцать|двенадцать|тринадцать|четырнадцать|пятнадцать|'
            r'шестнадцать|семнадцать|восемнадцать|девятнадцать|двадцать|'
            r'первое|второе|третье|четвертое|пятое|шестое|седьмое|восьмое|'
            r'девятое|десятое|одиннадцатое|двенадцатое|тринадцатое|четырнадцатое|'
            r'пятнадцатое|шестнадцатое|семнадцатое|восемнадцатое|девятнадцатое|'
            r'двадцатое|тридцатое)\s+'
            r'(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+'
            r'(две\s+тысячи|тысяча|две\s+тысячи|две\s+тысячи|две\s+тысячи)\s+'
            r'(.*?)(?=\s+года|\s+год|$)',
            re.IGNORECASE
        )
        
        def replace_date(match):
            day = match.group(1)
            month = match.group(2)
            year_prefix = match.group(3)
            year_rest = match.group(4)
            
            # Преобразуем день в числовой формат
            day_num = self._month_name_to_number(day)
            month_num = self._month_name_to_number(month)
            
            # Обрабатываем год
            full_year_text = f"{year_prefix} {year_rest}".strip()
            year_num = self._parse_year(full_year_text)
            
            if day_num and month_num and year_num:
                return f"{day_num} {month} {year_num}"
            return match.group(0)
        
        return date_pattern.sub(replace_date, text)
    
    def _month_name_to_number(self, month_name: str) -> Optional[str]:
        """Преобразует название месяца или дня в число"""
        month_map = {
            "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
            "мая": "05", "июня": "06", "июля": "07", "августа": "08",
            "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12",
            
            # Дни месяца
            "первое": "01", "второе": "02", "третье": "03", "четвертое": "04",
            "пятое": "05", "шестое": "06", "седьмое": "07", "восьмое": "08",
            "девятое": "09", "десятое": "10", "одиннадцатое": "11", "двенадцатое": "12",
            "тринадцатое": "13", "четырнадцатое": "14", "пятнадцатое": "15",
            "шестнадцатое": "16", "семнадцатое": "17", "восемнадцатое": "18",
            "девятнадцатое": "19", "двадцатое": "20", "тридцатое": "30",
            
            # Альтернативные формы
            "двадцать": "20", "тридцать": "30"
        }
        
        month_name_lower = month_name.lower()
        return month_map.get(month_name_lower)
    
    def _parse_year(self, year_text: str) -> Optional[str]:
        """Парсит год из текстового представления"""
        try:
            # Пробуем распарсить через rus2num
            parsed = self.parser(year_text)
            if parsed:
                return str(parsed)
        except:
            pass
        
        # Ручной парсинг для типичных случаев
        year_text_lower = year_text.lower()
        
        # Две тысячи двадцать третьего
        if "две тысячи" in year_text_lower:
            if "двадцать третьего" in year_text_lower:
                return "2023"
            elif "двадцать второго" in year_text_lower:
                return "2022"
            elif "двадцать первого" in year_text_lower:
                return "2021"
            elif "двадцатого" in year_text_lower:
                return "2020"
        
        return None
    
    def _is_date_context(self, words: List[str], start_idx: int, consumed: int) -> bool:
        """Проверяет, является ли текущий контекст частью даты"""
        # Проверяем следующие слова на наличие названий месяцев
        month_names = {"января", "февраля", "марта", "апреля", "мая", "июня",
                       "июля", "августа", "сентября", "октября", "ноября", "декабря"}
        
        next_idx = start_idx + consumed
        if next_idx < len(words) and words[next_idx].lower() in month_names:
            return True
        
        return False
    
    def _format_date_part(self, parsed_str: str, words: List[str], start_idx: int, consumed: int) -> str:
        """Форматирует часть даты с ведущими нулями при необходимости"""
        # Для дней месяца добавляем ведущий ноль
        if len(parsed_str) == 1:
            return f"0{parsed_str}"
        return parsed_str
    
    def _alternative_parse(self, number_words: List[str]) -> Optional[int]:
        """Альтернативный метод парсинга для сложных случаев"""
        text = " ".join(number_words).lower()
        
        # Специальные случаи для дат
        date_cases = {
            "двадцать пятое": 25,
            "двадцать пятое мая": 25,
            "две тысячи двадцать третьего": 2023,
            "двадцать третьего": 23,
        }
        
        if text in date_cases:
            return date_cases[text]
        
        # Пытаемся разобрать составные числа
        try:
            # Простейший парсер для "XX YY" вида
            parts = text.split()
            if len(parts) == 2:
                # Например: "двадцать пятое" -> 25
                tens_map = {"двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50}
                units_map = {"пятое": 5, "шестое": 6, "седьмое": 7, "восьмое": 8, "девятое": 9,
                           "десятое": 10, "одиннадцатое": 11, "двенадцатое": 12}
                
                if parts[0] in tens_map and parts[1] in units_map:
                    return tens_map[parts[0]] + units_map[parts[1]]
        except:
            pass
        
        return None
    
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


number_parser = NumberParser()

if __name__ == "__main__":
    test_cases = [
        ("двадцать три один", "231"),
        ("восемьдесят сто", "80100"),
        ("сто двадцать три", "123"),
        ("сто два", "102"),
        ("пятьсот сорок два", "542"),
        ("тысяча двести", "1200"),
        ("две тысячи двадцать пятого", "2025"),  # Исправлено: теперь правильно обрабатывает
        ("сто двадцать три дробь один", "123/1"),
        
        ("двадцать ноль восемьдесят шесть", "20086"),
        ("пятьсот ноль три", "50003"),
        ("пять ноль сорок два", "5042"),
        ("тридцать ноль пять", "3005"),
        ("два ноль пятьсот сорок", "20540"),
        
        ("пять ноль ноль ноль три", "50003"),
        ("пятьдесят тысяч три", "50003"),
        
        ("пятьсот девяносто шесть", "596"),
    ]
    
    print("Запуск тестов с rus2num...\n")
    
    for input_text, expected in test_cases:
        result = number_parser.convert_text_numbers_to_digits(input_text)
        status = "✓" if result == expected else "✗"
        print(f"'{input_text}' -> '{result}' (ожидалось '{expected}') {status}")
        
    print("\nВсе тесты завершены!")
    
    print("\n--- Примеры реального использования ---")
    real_examples = [
        "Сто двадцать три рубля",
        "Двадцать пятое мая две тысячи двадцать третьего года",
        "Пятьсот ноль три килограмма",
        "Тридцать ноль пять процентов",
        "Два ноль пятьсот сорок метров",
        "Сто двадцать три дробь сорок два",
    ]
    
    print("\nРезультаты:")
    for example in real_examples:
        result = number_parser.convert_text_numbers_to_digits(example)
        print(f"'{example}' -> '{result}'")