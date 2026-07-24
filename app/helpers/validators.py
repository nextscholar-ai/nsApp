# app/helpers/validators.py

import re
from datetime import date


class Validators:
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        return bool(re.match(r"^[0-9]{10}$", phone))

    @staticmethod
    def validate_pincode(pincode: str) -> bool:
        return bool(re.match(r"^[0-9]{6}$", pincode))

    @staticmethod
    def validate_blood_group(blood_group: str) -> bool:
        valid_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        return blood_group in valid_groups

    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> bool:
        return start_date <= end_date

    @staticmethod
    def validate_year_range(start_year: int, end_year: int) -> bool:
        return end_year > start_year

    @staticmethod
    def validate_marks(obtained: float, total: float) -> bool:
        return 0 <= obtained <= total

    @staticmethod
    def validate_percentage(value: float) -> bool:
        return 0 <= value <= 100
