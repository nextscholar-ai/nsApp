# app/helpers/date_utils.py

from datetime import datetime, date, timedelta
from typing import Optional

class DateUtils:
    @staticmethod
    def get_current_academic_year():
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        if current_month >= 4:  # April to December
            return current_year, current_year + 1
        else:  # January to March
            return current_year - 1, current_year

    @staticmethod
    def get_age_from_dob(dob: date) -> int:
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @staticmethod
    def get_week_number(date_obj: date) -> int:
        return date_obj.isocalendar()[1]

    @staticmethod
    def get_day_of_week(date_obj: date) -> str:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[date_obj.weekday()]

    @staticmethod
    def format_date_for_display(date_obj: date, format_str: str = "%d-%m-%Y"):
        return date_obj.strftime(format_str)

    @staticmethod
    def is_date_in_range(check_date: date, start_date: date, end_date: date) -> bool:
        return start_date <= check_date <= end_date

    @staticmethod
    def add_days(date_obj: date, days: int) -> date:
        return date_obj + timedelta(days=days)