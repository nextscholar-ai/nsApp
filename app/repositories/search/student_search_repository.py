# ============================================================
# app/repositories/search/student_search_repository.py
# ============================================================
#
# Responsibility: database queries, filtering, pagination, hydration.
# Nothing else - no similarity scoring, no ranking, no response
# shaping. See app/services/search/student_search_service.py for the
# layer that orchestrates this repository + the similarity engine.
#
# Every method reads directly from student_profiles/users (no cache/
# embedding table), so newly inserted or edited students are searchable
# immediately - there is nothing to reindex or refresh.

from typing import List, Optional, Sequence, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.helpers.search.text_utils import build_search_text
from app.model import StudentProfile, User


class StudentSearchRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_exact(self, normalized_query: str, raw_query: str) -> List[StudentProfile]:
        """Case-insensitive exact match across every field a user might
        type verbatim: name, student_id, admission/registration number,
        email, phone. Never assumes uniqueness - callers must expect and
        handle multiple rows back (e.g. two students both named "Mohammad
        Ali" both come back and both must be shown)."""
        return (
            self.db.query(StudentProfile)
            .join(User, User.id == StudentProfile.user_id)
            .options(joinedload(StudentProfile.user))
            .filter(
                StudentProfile.is_active == True,  # noqa: E712
                or_(
                    func.lower(StudentProfile.student_name) == normalized_query,
                    func.lower(StudentProfile.student_id) == normalized_query,
                    func.lower(StudentProfile.admission_number) == normalized_query,
                    func.lower(StudentProfile.registration_number) == normalized_query,
                    func.lower(User.email) == normalized_query,
                    User.phone == raw_query.strip(),
                ),
            )
            .all()
        )

    def get_fuzzy_name_pool(self, limit: int) -> List[Tuple[str, str]]:
        """Returns (student_id, searchable_text_blob) pairs for NAME/CODE
        fuzzy matching - deliberately excludes email so that a query for
        "priya" doesn't fuzzy-collide with every student who happens to
        share an email domain. Bounded by `limit` regardless of table
        size - see app/helpers/search/similarity_engine.py for the
        caller-side default."""
        rows = (
            self.db.query(
                StudentProfile.student_id,
                StudentProfile.student_name,
                StudentProfile.admission_number,
                StudentProfile.registration_number,
                StudentProfile.parent_name,
                StudentProfile.guardian_name,
            )
            .filter(StudentProfile.is_active == True)  # noqa: E712
            .limit(limit)
            .all()
        )

        return [
            (
                row.student_id,
                build_search_text(
                    row.student_name,
                    row.admission_number,
                    row.registration_number,
                    row.student_id,
                    row.parent_name,
                    row.guardian_name,
                ),
            )
            for row in rows
        ]

    def get_fuzzy_email_pool(self, limit: int) -> List[Tuple[str, str]]:
        """Returns (student_id, email) pairs, used only when the query
        looks like an email - lets a typo'd email ("mohamad.ahmed@gmial.com")
        still fuzzy-match the right account without polluting name search."""
        rows = (
            self.db.query(StudentProfile.student_id, User.email)
            .join(User, User.id == StudentProfile.user_id)
            .filter(StudentProfile.is_active == True, User.email.isnot(None))  # noqa: E712
            .limit(limit)
            .all()
        )
        return [(row.student_id, row.email) for row in rows]

    def get_by_ids(self, student_ids: Sequence[str]) -> List[StudentProfile]:
        if not student_ids:
            return []
        return (
            self.db.query(StudentProfile)
            .options(joinedload(StudentProfile.user))
            .filter(StudentProfile.student_id.in_(student_ids))
            .all()
        )

    def get_by_id(self, student_id: str) -> Optional[StudentProfile]:
        return (
            self.db.query(StudentProfile)
            .options(joinedload(StudentProfile.user))
            .filter(StudentProfile.student_id == student_id)
            .first()
        )
