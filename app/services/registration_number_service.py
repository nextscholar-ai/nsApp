from datetime import date

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.model import StudentProfile
from app.helpers.code_generators import generate_registration_number


class RegistrationNumberService:
    """Generates unique, human-searchable registration numbers
    (e.g. REG-2026-00001), scoped per calendar year.

    Sequence is derived from how many registration numbers already exist
    for that year, then generation retries on a rare unique-constraint
    collision (two concurrent signups in the same year) by bumping the
    sequence and trying again — the same defensive pattern already used
    elsewhere in this codebase (see generate_timetable_id usage).
    """

    MAX_ATTEMPTS = 5

    def __init__(self, db: Session):
        self.db = db

    def _next_sequence_for_year(self, year: int) -> int:
        prefix = f"REG-{year}-"
        count = (
            self.db.query(func.count(StudentProfile.student_id))
            .filter(StudentProfile.registration_number.like(f"{prefix}%"))
            .scalar()
        ) or 0
        return count + 1

    def generate_for_student(self, student: StudentProfile, *, commit: bool = True) -> str:
        """Assigns a registration_number to `student` if it doesn't already
        have one. Returns the (possibly pre-existing) registration_number.
        """
        if student.registration_number:
            return student.registration_number

        year = date.today().year
        last_error = None

        for attempt in range(self.MAX_ATTEMPTS):
            sequence = self._next_sequence_for_year(year) + attempt
            candidate = generate_registration_number(year, sequence)

            student.registration_number = candidate
            self.db.add(student)
            try:
                if commit:
                    self.db.commit()
                    self.db.refresh(student)
                else:
                    self.db.flush()
                return candidate
            except IntegrityError as exc:
                self.db.rollback()
                last_error = exc
                continue

        raise RuntimeError(
            f"Could not generate a unique registration number after "
            f"{self.MAX_ATTEMPTS} attempts"
        ) from last_error

    def backfill_missing_registration_numbers(self) -> dict:
        """Assigns registration numbers to every StudentProfile that
        doesn't have one yet. Safe to call repeatedly (e.g. on app
        startup) — students who already have one are skipped.
        """
        students = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.registration_number.is_(None))
            .all()
        )

        generated, failed = 0, 0
        for student in students:
            try:
                self.generate_for_student(student, commit=True)
                generated += 1
            except Exception:
                self.db.rollback()
                failed += 1

        return {"generated": generated, "failed": failed, "total_missing": len(students)}
