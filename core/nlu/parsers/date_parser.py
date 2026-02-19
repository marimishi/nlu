import re
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Dict, Optional, Tuple, Any, List
from utils.date_utils import format_date_iso


def is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


class DateParser:
    def __init__(self):
        self.current_date = datetime.now()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month
        
        self.months_data = {
            "январ": ("01", 31, "январь", "января"),
            "феврал": ("02", 28, "февраль", "февраля"),
            "март": ("03", 31, "март", "марта"),
            "апрел": ("04", 30, "апрель", "апреля"),
            "май": ("05", 31, "май", "мая"),
            "мае": ("05", 31, "май", "мая"),
            "июн": ("06", 30, "июнь", "июня"),
            "июл": ("07", 31, "июль", "июля"),
            "август": ("08", 31, "август", "августа"),
            "сентябр": ("09", 30, "сентябрь", "сентября"),
            "октябр": ("10", 31, "октябрь", "октября"),
            "ноябр": ("11", 30, "ноябрь", "ноября"),
            "декабр": ("12", 31, "декабрь", "декабря")
        }
        
        self.relative_periods = {
            "прошлый год": ("last_year", None),
            "прошлого года": ("last_year", None),
            "прошлом году": ("last_year", None),
            "прошлый месяц": ("last_month", None),
            "прошлого месяца": ("last_month", None),
            "прошлом месяце": ("last_month", None),
            "предыдущий год": ("last_year", None),
            "предыдущего года": ("last_year", None),
            "предыдущий месяц": ("last_month", None),
            "предыдущего месяца": ("last_month", None),
            "последний год": ("last_year", None),
            "последнего года": ("last_year", None),
            "последний месяц": ("last_month", None),
            "последнего месяца": ("last_month", None),
            "текущий год": ("current_year", None),
            "текущего года": ("current_year", None),
            "текущий месяц": ("current_month", None),
            "текущего месяца": ("current_month", None),
            "этот год": ("current_year", None),
            "этого года": ("current_year", None),
            "этот месяц": ("current_month", None),
            "этого месяца": ("current_month", None),
            "следующий год": ("next_year", None),
            "следующего года": ("next_year", None),
            "следующий месяц": ("next_month", None),
            "следующего месяца": ("next_month", None),
            "будущий год": ("next_year", None),
            "будущего года": ("next_year", None),
            "будущий месяц": ("next_month", None),
            "будущего месяца": ("next_month", None)
        }
        
        self.numerals = {
            "первое": 1, "первый": 1,
            "второе": 2, "второй": 2,
            "третье": 3, "третий": 3,
            "четвертое": 4, "четвертый": 4,
            "пятое": 5, "пятый": 5,
            "шестое": 6, "шестой": 6,
            "седьмое": 7, "седьмой": 7,
            "восьмое": 8, "восьмой": 8,
            "девятое": 9, "девятый": 9,
            "десятое": 10, "десятый": 10,
            "одиннадцатое": 11, "одиннадцатый": 11,
            "двенадцатое": 12, "двенадцатый": 12,
            "тринадцатое": 13, "тринадцатый": 13,
            "четырнадцатое": 14, "четырнадцатый": 14,
            "пятнадцатое": 15, "пятнадцатый": 15,
            "шестнадцатое": 16, "шестнадцатый": 16,
            "семнадцатое": 17, "семнадцатый": 17,
            "восемнадцатое": 18, "восемнадцатый": 18,
            "девятнадцатое": 19, "девятнадцатый": 19,
            "двадцатое": 20, "двадцатый": 20,
            "двадцать первое": 21, "двадцать первый": 21,
            "двадцать второе": 22, "двадцать второй": 22,
            "двадцать третье": 23, "двадцать третий": 23,
            "двадцать четвертое": 24, "двадцать четвертый": 24,
            "двадцать пятое": 25, "двадцать пятый": 25,
            "двадцать шестое": 26, "двадцать шестой": 26,
            "двадцать седьмое": 27, "двадцать седьмой": 27,
            "двадцать восьмое": 28, "двадцать восьмой": 28,
            "двадцать девятое": 29, "двадцать девятый": 29,
            "тридцатое": 30, "тридцатый": 30,
            "тридцать первое": 31, "тридцать первый": 31
        }
    
    def get_month_days(self, month_prefix: str, year: int) -> Optional[Tuple[str, int]]:
        if not month_prefix:
            return None
        month_data = self.months_data.get(month_prefix)
        if not month_data:
            return None
        
        month_num, days_normal, _, _ = month_data
        
        if month_prefix in ["феврал", "февраль"] and is_leap_year(year):
            return month_num, 29
        
        return month_num, days_normal
    
    def find_month_in_text(self, text: str) -> Optional[Tuple[str, str, int, str]]:
        if not text:
            return None
        text_lower = text.lower()
        
        for month_prefix, (month_num, days_normal, month_nom, month_gen) in self.months_data.items():
            if month_prefix in text_lower or month_nom in text_lower or month_gen in text_lower:
                return "month", month_num, days_normal, month_nom
        
        return None
    
    def find_relative_period_in_text(self, text: str) -> Optional[Tuple[str, str]]:
        if not text:
            return None
        text_lower = text.lower()
        
        for period_text, (period_type, _) in self.relative_periods.items():
            if period_text in text_lower:
                return period_type, period_text
        
        return None
    
    def extract_year_from_text(self, text: str) -> Optional[int]:
        if not text:
            return None
            
        year_match = re.search(r'\b(20\d{2})\b', text)
        if year_match:
            return int(year_match.group(1))
        
        year_match = re.search(r'(20\d{2})\s*(?:года|г\.?)', text)
        if year_match:
            return int(year_match.group(1))
        
        year_match = re.search(r'\b(\d{2})\b(?:\s*(?:года|г\.?))?', text)
        if year_match:
            short_year = int(year_match.group(1))
            if 0 <= short_year <= 99:
                if short_year <= self.current_year % 100:
                    return 2000 + short_year
                else:
                    return 1900 + short_year
        
        return None
    
    def parse_date_components(self, text: str) -> Dict[str, Any]:
        result = {
            "day": None,
            "month": None,
            "year": None,
            "relative_period": None,
            "period_text": None
        }
        
        if not text:
            return result
            
        text_lower = text.lower().strip()
        
        if text_lower.startswith("за "):
            text_lower = text_lower[2:].strip()
        
        relative_info = self.find_relative_period_in_text(text_lower)
        if relative_info:
            result["relative_period"], result["period_text"] = relative_info
        
        month_info = self.find_month_in_text(text_lower)
        if month_info:
            _, month_num, _, _ = month_info
            result["month"] = month_num
        
        result["year"] = self.extract_year_from_text(text_lower)
        
        for numeral, day_num in self.numerals.items():
            if numeral in text_lower:
                result["day"] = day_num
                break
        
        if result["day"] is None:
            number_match = re.search(r'\b(\d{1,2})\b', text_lower)
            if number_match:
                potential_day = int(number_match.group(1))
                if not (1900 <= potential_day <= 2100) and not re.search(r'\d{1,2}\.\d{1,2}', text_lower):
                    result["day"] = potential_day
        
        date_match = re.search(r'(\d{1,2})\.(\d{1,2})', text_lower)
        if date_match:
            result["day"] = int(date_match.group(1))
            month_from_date = int(date_match.group(2))
            result["month"] = f"{month_from_date:02d}"
        
        return result
    
    def calculate_relative_dates(self, relative_period: str, month: Optional[str] = None) -> Dict[str, str]:
        if relative_period == "last_year":
            last_year = self.current_year - 1
            return {
                "start": format_date_iso(date(last_year, 1, 1)),
                "end": format_date_iso(date(last_year, 12, 31))
            }
        
        elif relative_period == "current_year":
            return {
                "start": format_date_iso(date(self.current_year, 1, 1)),
                "end": format_date_iso(date(self.current_year, 12, 31))
            }
        
        elif relative_period == "next_year":
            next_year = self.current_year + 1
            return {
                "start": format_date_iso(date(next_year, 1, 1)),
                "end": format_date_iso(date(next_year, 12, 31))
            }
        
        elif relative_period == "last_month":
            last_month_date = self.current_date - relativedelta(months=1)
            last_month = last_month_date.month
            last_month_year = last_month_date.year
            
            if last_month == 2:
                last_day = 29 if is_leap_year(last_month_year) else 28
            elif last_month in [4, 6, 9, 11]:
                last_day = 30
            else:
                last_day = 31
            
            return {
                "start": format_date_iso(date(last_month_year, last_month, 1)),
                "end": format_date_iso(date(last_month_year, last_month, last_day))
            }
        
        elif relative_period == "current_month":
            current_month = self.current_date.month
            current_year = self.current_date.year
            current_day = self.current_date.day
            
            return {
                "start": format_date_iso(date(current_year, current_month, 1)),
                "end": format_date_iso(date(current_year, current_month, current_day))
            }
        
        elif relative_period == "next_month":
            next_month_date = self.current_date + relativedelta(months=1)
            next_month = next_month_date.month
            next_month_year = next_month_date.year
            
            if next_month == 2:
                last_day = 29 if is_leap_year(next_month_year) else 28
            elif next_month in [4, 6, 9, 11]:
                last_day = 30
            else:
                last_day = 31
            
            return {
                "start": format_date_iso(date(next_month_year, next_month, 1)),
                "end": format_date_iso(date(next_month_year, next_month, last_day))
            }
        
        return {"start": "", "end": ""}
    
    def calculate_month_dates(self, month: str, year: int, day: Optional[int] = None) -> Dict[str, str]:
        if not month or not year:
            return {"start": "", "end": ""}
            
        month_prefix = None
        for prefix, (m_num, _, month_nom, _) in self.months_data.items():
            if m_num == month:
                month_prefix = prefix
                break
        
        if not month_prefix:
            return {"start": "", "end": ""}
        
        month_data = self.get_month_days(month_prefix, year)
        if not month_data:
            return {"start": "", "end": ""}
        
        month_num, last_day = month_data
        
        if day is not None:
            if day > last_day:
                day = last_day
            try:
                date_obj = date(year, int(month_num), day)
                date_str = format_date_iso(date_obj)
                return {"start": date_str, "end": date_str}
            except ValueError:
                return {"start": "", "end": ""}
        else:
            try:
                return {
                    "start": format_date_iso(date(year, int(month_num), 1)),
                    "end": format_date_iso(date(year, int(month_num), last_day))
                }
            except ValueError:
                return {"start": "", "end": ""}
    
    def parse_period(self, period_text: str) -> Dict[str, str]:
        if not period_text:
            return {"start": "", "end": ""}
        
        try:
            print(f"DateParser input: '{period_text}'")
            
            text_lower = period_text.lower()
            
            month_pattern = r'(январ[ья]?|феврал[ья]?|март[а]?|апрел[ья]?|ма[йя]|июн[ья]?|июл[ья]?|август[а]?|сентябр[ья]?|октябр[ья]?|ноябр[ья]?|декабр[ья]?)'
            year_pattern = r'(прошлого\s+года|прошлый\s+год|прошлом\s+году)'
            
            combined_pattern = f"{month_pattern}.*{year_pattern}"
            if re.search(combined_pattern, text_lower, re.IGNORECASE):
                print("Detected pattern: month + last year")
                month_match = re.search(month_pattern, text_lower, re.IGNORECASE)
                if month_match:
                    month_text = month_match.group(1)
                    for prefix, (month_num, _, month_nom, month_gen) in self.months_data.items():
                        if (prefix in month_text or 
                            month_nom in month_text or 
                            month_gen in month_text or
                            month_text in [prefix, month_nom, month_gen]):
                            year = self.current_year - 1
                            dates = self.calculate_month_dates(month_num, year)
                            print(f"DateParser result (month + last year): {dates}")
                            return dates
            
            month_year_pattern = f"{month_pattern}\s*(20\d{{2}})"
            month_year_match = re.search(month_year_pattern, text_lower, re.IGNORECASE)
            if month_year_match:
                print("Detected pattern: month + year")
                month_text = month_year_match.group(1)
                year = int(month_year_match.group(2))
                for prefix, (month_num, _, month_nom, month_gen) in self.months_data.items():
                    if (prefix in month_text or 
                        month_nom in month_text or 
                        month_gen in month_text or
                        month_text in [prefix, month_nom, month_gen]):
                        dates = self.calculate_month_dates(month_num, year)
                        print(f"DateParser result (month + year): {dates}")
                        return dates
            
            if re.search(r'прошлого\s+года|прошлый\s+год|прошлом\s+году', text_lower, re.IGNORECASE):
                if not re.search(month_pattern, text_lower, re.IGNORECASE):
                    print("Detected pattern: last year only")
                    last_year = self.current_year - 1
                    dates = {
                        "start": format_date_iso(date(last_year, 1, 1)),
                        "end": format_date_iso(date(last_year, 12, 31))
                    }
                    print(f"DateParser result (last year only): {dates}")
                    return dates
            
            components = self.parse_date_components(period_text)
            print(f"DateParser components: {components}")
            
            year = None
            if components.get("relative_period"):
                if "year" in components["relative_period"]:
                    if components["relative_period"] == "last_year":
                        year = self.current_year - 1
                    elif components["relative_period"] == "next_year":
                        year = self.current_year + 1
                    elif components["relative_period"] == "current_year":
                        year = self.current_year
                elif "month" in components["relative_period"] and not components.get("month"):
                    dates = self.calculate_relative_dates(components["relative_period"])
                    print(f"DateParser result (relative month only): {dates}")
                    return dates
            
            if year is None and components.get("relative_period"):
                year = self.current_year
            
            if year is None:
                year = components.get("year") or self.current_year
            
            if components.get("month"):
                if components.get("relative_period") == "last_year":
                    year = self.current_year - 1
                elif components.get("relative_period") == "next_year":
                    year = self.current_year + 1
                
                dates = self.calculate_month_dates(
                    components["month"],
                    year,
                    components.get("day")
                )
                print(f"DateParser result (month with year): {dates}")
                return dates
            
            if components.get("relative_period") and "year" in components["relative_period"]:
                dates = self.calculate_relative_dates(components["relative_period"])
                print(f"DateParser result (relative year): {dates}")
                return dates
            
            print(f"DateParser: could not determine dates")
            return {"start": "", "end": ""}
            
        except Exception as e:
            print(f"Error parsing period '{period_text}': {e}")
            return {"start": "", "end": ""}


date_parser = DateParser()