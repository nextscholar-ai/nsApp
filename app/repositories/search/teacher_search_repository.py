# ============================================================
# app/repositories/search/teacher_search_repository.py
# ============================================================
#
# Same shape as StudentSearchRepository - see that file's module
# docstring for the layer's overall responsibility. Kept as its own
# class (rather than a generic "PersonSearchRepository") because each
# entity's exact-match/fuzzy-pool columns are genuinely different
# (teachers have employee_code, department, designation; students have
# admission/registration numbers) and forcing a shared base class here
# would trade a small amount of duplication for a much harder to follow
# indirection. app/helpers/search/* is where the actually-shared logic
# lives.

from collections.abc import Sequence

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.helpers.search.text_utils import build_search_text
from app.model import TeacherProfile, User


class TeacherSearchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_exact(self, normalized_query: str, raw_query: str) -> list[TeacherProfile]:
        return (
            self.db.query(TeacherProfile)
            .join(User, User.id == TeacherProfile.user_id)
            .options(joinedload(TeacherProfile.user))
            .filter(
                TeacherProfile.is_active == True,  # noqa: E712
                or_(
                    func.lower(TeacherProfile.teacher_name) == normalized_query,
                    func.lower(TeacherProfile.teacher_id) == normalized_query,
                    func.lower(TeacherProfile.employee_code) == normalized_query,
                    func.lower(User.email) == normalized_query,
                    User.phone == raw_query.strip(),
                ),
            )
            .all()
        )

    def get_fuzzy_name_pool(self, limit: int) -> list[tuple[str, str]]:
        rows = (
            self.db.query(
                TeacherProfile.teacher_id,
                TeacherProfile.teacher_name,
                TeacherProfile.employee_code,
                TeacherProfile.designation,
                TeacherProfile.department,
            )
            .filter(TeacherProfile.is_active == True)  # noqa: E712
            .limit(limit)
            .all()
        )

        return [
            (
                row.teacher_id,
                build_search_text(
                    row.teacher_name,
                    row.employee_code,
                    row.teacher_id,
                    row.designation,
                    row.department,
                ),
            )
            for row in rows
        ]

    def get_fuzzy_email_pool(self, limit: int) -> list[tuple[str, str]]:
        rows = (
            self.db.query(TeacherProfile.teacher_id, User.email)
            .join(User, User.id == TeacherProfile.user_id)
            .filter(TeacherProfile.is_active == True, User.email.isnot(None))  # noqa: E712
            .limit(limit)
            .all()
        )
        return [(row.teacher_id, row.email) for row in rows]

    def get_by_ids(self, teacher_ids: Sequence[str]) -> list[TeacherProfile]:
        if not teacher_ids:
            return []
        return (
            self.db.query(TeacherProfile)
            .options(joinedload(TeacherProfile.user))
            .filter(TeacherProfile.teacher_id.in_(teacher_ids))
            .all()
        )

    def get_by_id(self, teacher_id: str) -> TeacherProfile | None:
        return (
            self.db.query(TeacherProfile)
            .options(joinedload(TeacherProfile.user))
            .filter(TeacherProfile.teacher_id == teacher_id)
            .first()
        )
