# ============================================================
# app/services/identifier_resolver_service.py
# ============================================================
#
# Har jagah jahan pehle sirf raw student_id / teacher_id (business id
# string, e.g. "STU2026001") accept hota tha, ab wahi field NAME, EMAIL,
# ya ID -- teeno me se kuch bhi accept kar sakta hai. Andar (DB me),
# kaam hamesha asli business id se hi hota hai -- sirf USER ke liye
# typing/searching aasan ho gayi hai.
#
# Resolution order (jo pehle match kare, wahi use hota hai):
#   1. Exact business id match      (student_id / teacher_id column)
#   2. Exact email match            (case-insensitive)
#   3. Name match                   (case-insensitive)
#        - 1 match  -> seedha resolve ho jata hai
#        - 0 match  -> IdentifierNotFoundError
#        - 2+ match -> AmbiguousIdentifierError (candidates list ke
#          saath -- caller/router isko 409 me convert karta hai taaki
#          frontend ek chhoti si list dikha sake aur user sahi wala
#          chun sake)
#
# Ye service kisi bhi router/service me use ho sakti hai:
#
#     from app.services.identifier_resolver_service import IdentifierResolverService
#
#     resolver = IdentifierResolverService(db)
#     student = resolver.resolve_student(student_id)   # returns StudentProfile
#     real_id = student.student_id                      # ab yahi id aage use karo
#
# ============================================================

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.model import User, StudentProfile, TeacherProfile, StudentClass, ClassRoom
from app.core.exceptions import AmbiguousIdentifierError, IdentifierNotFoundError


class IdentifierResolverService:

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------
    # STUDENT
    # ------------------------------------------------------------

    def resolve_student(self, identifier: str) -> StudentProfile:
        """Accepts student_id, email, or student_name. Returns the
        matching StudentProfile, or raises IdentifierNotFoundError /
        AmbiguousIdentifierError."""

        if identifier is None or not identifier.strip():
            raise IdentifierNotFoundError("Student identifier is empty")

        value = identifier.strip()

        # 1) Exact business id (fully backward compatible: existing
        #    frontend code that already sends a real student_id keeps
        #    working exactly as before, with zero extra DB round trips
        #    for the common case).
        student = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.student_id == value)
            .first()
        )
        if student:
            return student

        # 2) Exact email match (email is unique, so this is always safe)
        student = (
            self.db.query(StudentProfile)
            .join(User, User.id == StudentProfile.user_id)
            .filter(func.lower(User.email) == value.lower())
            .first()
        )
        if student:
            return student

        # 3) Name match
        matches: List[StudentProfile] = (
            self.db.query(StudentProfile)
            .filter(func.lower(StudentProfile.student_name) == value.lower())
            .all()
        )

        if not matches:
            # fall back to partial/contains match so small typos or
            # partial names still surface candidates instead of a
            # hard dead-end
            matches = (
                self.db.query(StudentProfile)
                .filter(StudentProfile.student_name.ilike(f"%{value}%"))
                .all()
            )

        if not matches:
            raise IdentifierNotFoundError(
                f"No student found matching '{identifier}' (tried id, email, name)"
            )

        if len(matches) == 1:
            return matches[0]

        raise AmbiguousIdentifierError(
            f"'{identifier}' matches {len(matches)} students. Please pick one.",
            candidates=[self._student_candidate(s) for s in matches],
        )

    def resolve_student_id(self, identifier: str) -> str:
        """Convenience wrapper: returns just the resolved student_id string."""
        return self.resolve_student(identifier).student_id

    def _student_candidate(self, student: StudentProfile) -> dict:
        email = student.user.email if student.user else None

        active_class = (
            self.db.query(ClassRoom.display_name)
            .join(StudentClass, StudentClass.classroom_id == ClassRoom.id)
            .filter(StudentClass.student_id == student.student_id, StudentClass.status == "ACTIVE")
            .order_by(StudentClass.admission_date.desc())
            .first()
        )

        return {
            "student_id": student.student_id,
            "student_name": student.student_name,
            "email": email,
            "class_name": active_class[0] if active_class else None,
            "admission_number": student.admission_number,
        }

    # ------------------------------------------------------------
    # TEACHER
    # ------------------------------------------------------------

    def resolve_teacher(self, identifier: str) -> TeacherProfile:
        """Accepts teacher_id, email, or teacher_name. Returns the
        matching TeacherProfile, or raises IdentifierNotFoundError /
        AmbiguousIdentifierError."""

        if identifier is None or not identifier.strip():
            raise IdentifierNotFoundError("Teacher identifier is empty")

        value = identifier.strip()

        # 1) Exact business id
        teacher = (
            self.db.query(TeacherProfile)
            .filter(TeacherProfile.teacher_id == value)
            .first()
        )
        if teacher:
            return teacher

        # 2) Exact email match
        teacher = (
            self.db.query(TeacherProfile)
            .join(User, User.id == TeacherProfile.user_id)
            .filter(func.lower(User.email) == value.lower())
            .first()
        )
        if teacher:
            return teacher

        # 3) Name match
        matches: List[TeacherProfile] = (
            self.db.query(TeacherProfile)
            .filter(func.lower(TeacherProfile.teacher_name) == value.lower())
            .all()
        )

        if not matches:
            matches = (
                self.db.query(TeacherProfile)
                .filter(TeacherProfile.teacher_name.ilike(f"%{value}%"))
                .all()
            )

        if not matches:
            raise IdentifierNotFoundError(
                f"No teacher found matching '{identifier}' (tried id, email, name)"
            )

        if len(matches) == 1:
            return matches[0]

        raise AmbiguousIdentifierError(
            f"'{identifier}' matches {len(matches)} teachers. Please pick one.",
            candidates=[self._teacher_candidate(t) for t in matches],
        )

    def resolve_teacher_id(self, identifier: str) -> str:
        """Convenience wrapper: returns just the resolved teacher_id string."""
        return self.resolve_teacher(identifier).teacher_id

    def _teacher_candidate(self, teacher: TeacherProfile) -> dict:
        email = teacher.user.email if teacher.user else None
        return {
            "teacher_id": teacher.teacher_id,
            "teacher_name": teacher.teacher_name,
            "email": email,
            "department": teacher.department,
            "designation": teacher.designation,
        }
