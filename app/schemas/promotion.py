from datetime import date

from .common import BaseSchema


class StudentPromotionHistoryBase(BaseSchema):
    student_id: str
    from_session_id: str
    to_session_id: str
    from_classroom_id: str
    to_classroom_id: str
    previous_roll_number: int
    new_roll_number: int
    promotion_date: date | None = None
    promotion_type: str = "PROMOTED"
    remarks: str | None = None


class StudentPromotionHistoryCreate(StudentPromotionHistoryBase):
    pass


class StudentPromotionHistoryUpdate(BaseSchema):
    from_session_id: str | None = None
    to_session_id: str | None = None
    from_classroom_id: str | None = None
    to_classroom_id: str | None = None
    previous_roll_number: int | None = None
    new_roll_number: int | None = None
    promotion_date: date | None = None
    promotion_type: str | None = None
    remarks: str | None = None


class StudentPromotionHistoryResponse(StudentPromotionHistoryBase):
    promotion_code: str
    promoted_by_user_id: str | None = None
