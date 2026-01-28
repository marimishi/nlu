from datetime import datetime, date
from typing import Optional


def is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def get_last_day_of_month(year: int, month: int) -> int:
    if month == 2:
        return 29 if is_leap_year(year) else 28
    elif month in [4, 6, 9, 11]:
        return 30
    else:
        return 31


def format_date_iso(date_obj: Optional[date]) -> str:
    if not date_obj:
        return ""
    return date_obj.strftime("%Y-%m-%d")


def format_date_dd_mm_yyyy(date_obj: Optional[date]) -> str:
    if not date_obj:
        return ""
    return date_obj.strftime("%d.%m.%Y")