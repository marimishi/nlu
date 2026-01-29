import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, Optional, Tuple, Any


def is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


class DateParser:
    def __init__(self):
        self.current_date = datetime.now()
        self.current_year = self.current_date.year
        
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
        month_data = self.months_data.get(month_prefix)
        if not month_data:
            return None
        
        month_num, days_normal, _, _ = month_data
        
        if month_prefix in ["феврал", "февраль"] and is_leap_year(year):
            return month_num, 29
        
        return month_num, days_normal
    
    def find_month_in_text(self, text: str) -> Optional[Tuple[str, str, int, str]]:
        text_lower = text.lower()
        
        special_periods = {
            "текущий месяц": ("current", "01", 31, "текущий месяц"),
            "этот месяц": ("current", "01", 31, "этот месяц"),
            "прошлый месяц": ("last", "01", 31, "прошлый месяц"),
            "предыдущий месяц": ("last", "01", 31, "предыдущий месяц"),
            "последний месяц": ("last", "01", 31, "последний месяц"),
            "следующий месяц": ("next", "01", 31, "следующий месяц")
        }
        
        for period_text, (period_type, month_num, days, display_name) in special_periods.items():
            if period_text in text_lower:
                return period_type, month_num, days, display_name
        
        for month_prefix, (month_num, days_normal, month_nom, month_gen) in self.months_data.items():
            if month_prefix in text_lower or month_nom in text_lower or month_gen in text_lower:
                return "month", month_num, days_normal, month_nom
        
        return None
    
    def extract_year_from_text(self, text: str) -> Optional[int]:
        year_match = re.search(r'(20\d{2})', text)
        if year_match:
            return int(year_match.group(1))
        
        year_match_short = re.search(r'(20\d{2})\s*(?:года|г\.?)', text)
        if year_match_short:
            return int(year_match_short.group(1))
        
        return None
    
    def parse_date_components(self, text: str) -> Dict[str, Any]:
        result = {
            "day": None,
            "month": None,
            "year": None,
            "period_type": None,
            "special_period": None
        }
        
        text_lower = text.lower().strip()
        
        if text_lower.startswith("за "):
            text_lower = text_lower[2:].strip()
        
        month_info = self.find_month_in_text(text_lower)
        if month_info:
            period_type, month_num, days, display_name = month_info
            
            if period_type in ["current", "last", "next"]:
                result["special_period"] = f"{period_type}_month"
                result["period_type"] = "special"
            else:
                result["month"] = month_num
                result["period_type"] = "month"
        
        result["year"] = self.extract_year_from_text(text_lower)
        
        if result["year"] is None:
            if result["special_period"]:
                if result["special_period"] == "last_month":
                    if self.current_date.month == 1:
                        result["year"] = self.current_year - 1
                    else:
                        result["year"] = self.current_year
                else:
                    result["year"] = self.current_year
            elif result["month"]:
                target_month = int(result["month"])
                current_month = self.current_date.month
                
                if target_month > current_month:
                    result["year"] = self.current_year - 1
                else:
                    result["year"] = self.current_year
            else:
                result["year"] = self.current_year
        
        if not result["special_period"]:
            for numeral, day_num in self.numerals.items():
                if numeral in text_lower:
                    result["day"] = day_num
                    result["period_type"] = "date"
                    break
            
            if result["day"] is None:
                number_match = re.search(r'\b(\d{1,2})\b', text_lower)
                if number_match and not re.search(r'20\d{2}', number_match.group(1)):
                    result["day"] = int(number_match.group(1))
                    result["period_type"] = "date"
            
            date_match = re.search(r'(\d{1,2})\.(\d{1,2})', text_lower)
            if date_match:
                result["day"] = int(date_match.group(1))
                month_from_date = int(date_match.group(2))
                result["month"] = f"{month_from_date:02d}"
                result["period_type"] = "date"
                
                if result["year"] is None:
                    if month_from_date > self.current_date.month:
                        result["year"] = self.current_year - 1
                    else:
                        result["year"] = self.current_year
        
        return result
        
    def calculate_dates(self, day: Optional[int], month: str, year: int, 
                       period_type: str, special_period: Optional[str] = None) -> Dict[str, str]:
        
        if special_period == "current_month":
            current_month = self.current_date.strftime("%m")
            current_year = self.current_date.year
            current_day = self.current_date.day
            
            return {
                "start": f"01.{current_month}.{current_year}",
                "end": f"{current_day:02d}.{current_month}.{current_year}"
            }
        
        elif special_period == "last_month":
            last_month_date = self.current_date - relativedelta(months=1)
            last_month = last_month_date.strftime("%m")
            last_month_year = last_month_date.year
            
            if last_month_date.month == 2:
                if is_leap_year(last_month_year):
                    last_day_last = 29
                else:
                    last_day_last = 28
            elif last_month_date.month in [4, 6, 9, 11]:
                last_day_last = 30
            else:
                last_day_last = 31
            
            return {
                "start": f"01.{last_month}.{last_month_year}",
                "end": f"{last_day_last}.{last_month}.{last_month_year}"
            }
        
        elif special_period == "next_month":
            next_month_date = self.current_date + relativedelta(months=1)
            next_month = next_month_date.strftime("%m")
            next_month_year = next_month_date.year
            
            if next_month_date.month == 2:
                if is_leap_year(next_month_year):
                    last_day_next = 29
                else:
                    last_day_next = 28
            elif next_month_date.month in [4, 6, 9, 11]:
                last_day_next = 30
            else:
                last_day_next = 31
            
            return {
                "start": f"01.{next_month}.{next_month_year}",
                "end": f"{last_day_next}.{next_month}.{next_month_year}"
            }
        
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
        
        if period_type == "date" and day is not None:
            if day > last_day:
                day = last_day
            date_str = f"{day:02d}.{month_num}.{year}"
            return {"start": date_str, "end": date_str}
        
        elif period_type == "month":
            current_date = self.current_date
            if int(month_num) == current_date.month and year == current_date.year:
                return {
                    "start": f"01.{month_num}.{year}",
                    "end": f"{current_date.day:02d}.{month_num}.{year}"
                }
            else:
                return {
                    "start": f"01.{month_num}.{year}",
                    "end": f"{last_day}.{month_num}.{year}"
                }
        
        return {"start": "", "end": ""}
    
    def parse_period(self, period_text: str) -> Dict[str, str]:
        if not period_text:
            return {"start": "", "end": ""}
        
        try:
            components = self.parse_date_components(period_text)
            
            if components["special_period"]:
                return self.calculate_dates(
                    components["day"],
                    components["month"] or "01",
                    components["year"],
                    components["period_type"],
                    components["special_period"]
                )
            
            if components["month"] is None or components["year"] is None:
                return {"start": "", "end": ""}
            
            dates = self.calculate_dates(
                components["day"],
                components["month"],
                components["year"],
                components["period_type"] or "month"
            )
            
            return dates
            
        except Exception as e:
            print(f"Error parsing period '{period_text}': {e}")
            return {"start": "", "end": ""}


date_parser = DateParser()