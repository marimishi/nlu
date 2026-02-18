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

    # ================== PUBLIC ==================

    def parse_number(self, text: str) -> Optional[Union[int, str]]:
        if not text:
            return None

        text = text.lower().strip()

        if "дробь" in text:
            return self._parse_fraction(text)

        return self._parse_cardinal(text)

    def convert_text_numbers_to_digits(self, text: str) -> str:
        if not text:
            return text

        # сначала пробуем дробь
        if "дробь" in text.lower():
            frac = self._convert_fraction(text)
            if frac != text:
                return frac

        words = text.split()
        result_words = []
        i = 0

        while i < len(words):
            phrase = []
            j = i

            while j < len(words) and self._is_number_word(words[j].lower()):
                phrase.append(words[j])
                j += 1

            if phrase:
                parsed = self.parse_number(" ".join(phrase))
                if parsed is not None:
                    result_words.append(str(parsed))
                    i = j
                    continue

            result_words.append(words[i])
            i += 1

        return " ".join(result_words)

    def extract_numbers(self, text: str) -> List[tuple]:
        results = []
        words = text.lower().split()
        i = 0

        while i < len(words):
            phrase = []
            j = i

            while j < len(words) and self._is_number_word(words[j]):
                phrase.append(words[j])
                j += 1

            if phrase:
                parsed = self._parse_cardinal(" ".join(phrase))
                if parsed is not None:
                    results.append((" ".join(phrase), parsed))
                i = j
            else:
                i += 1

        return results

    # ================== INTERNAL ==================

    def _parse_cardinal(self, text: str) -> Optional[int]:
        words = text.split()
        if not words:
            return None

        total = 0
        current = 0

        for word in words:
            if word in self.thousands:
                if current == 0:
                    current = 1
                total += current * 1000
                current = 0

            elif word in self.hundreds:
                current += self.hundreds[word]

            elif word in self.tens:
                current += self.tens[word]

            elif word in self.teens:
                current += self.teens[word]

            elif word in self.digits:
                current += self.digits[word]

            else:
                return None

        return total + current if (total + current) > 0 else None

    def _parse_fraction(self, text: str) -> Optional[str]:
        m = re.match(r"(.+?)\s+дробь\s+(.+)", text)
        if not m:
            return None

        num = self._parse_cardinal(m.group(1))
        den = self._parse_cardinal(m.group(2))

        if num is None or den is None:
            return None

        return f"{num}/{den}"

    def _convert_fraction(self, text: str) -> str:
        m = re.search(r"(.+?)\s+дробь\s+(.+)", text, re.IGNORECASE)
        if not m:
            return text

        parsed = self._parse_fraction(text.lower())
        return parsed if parsed else text

    def _is_number_word(self, word: str) -> bool:
        return (
            word in self.digits
            or word in self.teens
            or word in self.tens
            or word in self.hundreds
            or word in self.thousands
        )


number_parser = NumberParser()