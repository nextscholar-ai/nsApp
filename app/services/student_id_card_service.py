from datetime import date, timedelta
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.model import (
    AcademicSession,
    ClassRoom,
    StudentClass,
    StudentIDCard,
    StudentProfile,
)
from app.services.utils.id_card_pdf_generator import render_student_id_pdf
from app.services.utils.id_card_qr_generator import generate_qr_image
from app.services.utils.institute_assets import load_institute_asset


class StudentIDCardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _paginate(self, page: int, page_size: int) -> tuple[int, int, int]:
        offset = (page - 1) * page_size
        return offset, page_size, page

    def _get_current_student(
        self,
        current_user,
        student_profile: StudentProfile | None = None,
    ):
        # current_user.role is already enforced by router dependencies
        if student_profile is not None:
            return student_profile
        return (
            self.db.query(StudentProfile)
            .filter(StudentProfile.user_id == current_user.id)
            .first()
        )

    def _get_academic_session_for_card(self) -> AcademicSession:
        session = (
            self.db.query(AcademicSession).filter(AcademicSession.is_current).first()
        )
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Current academic session not found",
            )
        return session

    def _compute_doj_and_valid_till(
        self,
        student_class: StudentClass,
    ) -> tuple[date | None, date | None]:
        doj = student_class.admission_date
        # Fixed policy: valid for 1 year from DOJ
        valid_till = None
        if doj:
            valid_till = doj + timedelta(days=365)
        return doj, valid_till

    @staticmethod
    def _profile_is_complete(student: StudentProfile) -> bool:
        """Minimal data required to render a card: name, DOB and parent name."""
        return bool(
            student.student_name and student.date_of_birth and student.parent_name,
        )

    def generate_or_regenerate_card(
        self,
        *,
        student_id: str,
        admin_user,
        regenerate: bool,
    ) -> StudentIDCard:
        if admin_user.role not in (UserRole.ADMIN.value, UserRole.ADMIN):
            # safety
            raise HTTPException(status_code=403, detail="Admin only")

        return self._generate_or_regenerate_card_internal(
            student_id=student_id,
            actor_user_id=admin_user.id,
            regenerate=regenerate,
        )

    def _generate_or_regenerate_card_internal(
        self,
        *,
        student_id: str,
        actor_user_id: int | None,
        regenerate: bool,
    ) -> StudentIDCard:
        """Core generation logic shared by the admin-triggered endpoint and the
        automated backfill routine. Raises HTTPException on failure so callers
        that want a hard failure (the API route) get one, while the backfill
        routine catches these per-student and continues with the rest.
        """
        student = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .first()
        )
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        current_session = self._get_academic_session_for_card()

        # Get student's active class in current academic session for class_display_name and DOJ
        student_class = (
            self.db.query(StudentClass)
            .filter(
                StudentClass.student_id == student.student_id,
                StudentClass.academic_sessions_id == current_session.session_code,
                StudentClass.status == "ACTIVE",
            )
            .first()
        )
        if not student_class:
            raise HTTPException(
                status_code=404,
                detail="Student not enrolled in current academic session",
            )

        classroom = (
            self.db.query(ClassRoom)
            .filter(ClassRoom.class_code == student_class.classroom_id)
            .first()
        )

        # Ensure assets
        institute_logo_path, institute_name, institute_contact = load_institute_asset()

        existing = (
            self.db.query(StudentIDCard)
            .filter(
                StudentIDCard.student_id == student.student_id,
                StudentIDCard.academic_sessions_id == current_session.session_code,
            )
            .first()
        )

        if existing and not regenerate:
            return existing

        # storage
        base_dir = (
            Path("uploads")
            / "student_id_cards"
            / str(current_session.session_code)
            / str(student.student_id)
        )
        base_dir.mkdir(parents=True, exist_ok=True)

        qr_path = str(base_dir / "qr.png")
        pdf_path = str(base_dir / "student_id_card.pdf")

        qr_payload = f"SCHOOL_ERP|student_id={student.student_id}|session_id={current_session.session_code}|card_type=STUDENT_ID"
        generate_qr_image(qr_payload, qr_path)

        doj, valid_till = self._compute_doj_and_valid_till(student_class)

        render_student_id_pdf(
            {
                "institute_logo_path": institute_logo_path,
                "institute_name": institute_name,
                "institute_contact_number": institute_contact,
                "academic_session_label": current_session.session_name,
                "date_of_joining": doj,
                "valid_till": valid_till,
                "student_photo_path": student.profile_photo,
                "student_name": student.student_name,
                "parent_name": student.parent_name,
                "class_display_name": classroom.display_name if classroom else None,
                "student_id_business": student.student_id,
                "qr_code_path": qr_path,
            },
            pdf_path,
        )

        if existing:
            existing.institute_logo_path = institute_logo_path
            existing.institute_name = institute_name
            existing.institute_contact_number = institute_contact
            existing.academic_session_label = current_session.session_name
            existing.date_of_joining = doj
            existing.valid_till = valid_till
            existing.student_photo_path = student.profile_photo
            existing.student_name = student.student_name
            existing.parent_name = student.parent_name
            existing.class_display_name = classroom.display_name if classroom else None
            existing.qr_code_path = qr_path
            existing.pdf_path = pdf_path
            existing.student_id_business = student.student_id
            self.db.commit()
            self.db.refresh(existing)
            return existing

        card = StudentIDCard(
            student_id=student.student_id,
            academic_sessions_id=current_session.session_code,
            student_name=student.student_name,
            parent_name=student.parent_name,
            class_display_name=classroom.display_name if classroom else None,
            institute_name=institute_name,
            institute_contact_number=institute_contact,
            academic_session_label=current_session.session_name,
            date_of_joining=doj,
            valid_till=valid_till,
            institute_logo_path=institute_logo_path,
            student_photo_path=student.profile_photo,
            qr_code_path=qr_path,
            pdf_path=pdf_path,
            student_id_business=student.student_id,
            created_by=actor_user_id,
            updated_by=actor_user_id,
        )

        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return card

    def backfill_missing_id_cards(self, *, actor_user_id: int | None = None) -> dict:
        """Iterate over every ACTIVE enrollment in the current academic session
        and generate an ID card for any student that doesn't already have one.

        Safe to call repeatedly (e.g. on application startup): students who
        already have a card, or whose profile is not yet complete enough to
        render one, are simply skipped rather than causing a failure.
        """
        try:
            current_session = self._get_academic_session_for_card()
        except HTTPException:
            # No current academic session configured yet - nothing to backfill.
            return {"generated": 0, "skipped": 0, "failed": 0}

        enrollments = (
            self.db.query(StudentClass)
            .filter(
                StudentClass.academic_sessions_id == current_session.session_code,
                StudentClass.status == "ACTIVE",
            )
            .all()
        )

        generated, skipped, failed = 0, 0, 0

        for enrollment in enrollments:
            existing = (
                self.db.query(StudentIDCard)
                .filter(
                    StudentIDCard.student_id == enrollment.student_id,
                    StudentIDCard.academic_sessions_id == current_session.session_code,
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            student = (
                self.db.query(StudentProfile)
                .filter(StudentProfile.student_id == enrollment.student_id)
                .first()
            )
            if not student or not self._profile_is_complete(student):
                # Profile not ready yet - it will be picked up on a later run
                # (e.g. next startup, or an explicit admin trigger) once complete.
                skipped += 1
                continue

            try:
                self._generate_or_regenerate_card_internal(
                    student_id=enrollment.student_id,
                    actor_user_id=actor_user_id,
                    regenerate=False,
                )
                generated += 1
            except Exception:
                # Never let one bad record stop the whole backfill run.
                self.db.rollback()
                failed += 1

        return {"generated": generated, "skipped": skipped, "failed": failed}

    def get_card_for_view(self, *, student_id: str, current_user) -> StudentIDCard:
        student_profile = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.user_id == current_user.id)
            .first()
        )
        if not student_profile and current_user.role == UserRole.STUDENT.value:
            raise HTTPException(status_code=404, detail="Student profile not found")

        # Admin/Teacher can view any; Student can view own only
        if (
            current_user.role == UserRole.STUDENT.value
            and student_profile.student_id != student_id
        ):
            raise HTTPException(
                status_code=403,
                detail="You can only view your own card",
            )

        card = (
            self.db.query(StudentIDCard)
            .filter(StudentIDCard.student_id == student_id)
            .order_by(StudentIDCard.academic_sessions_id.desc())
            .first()
        )
        if not card:
            raise HTTPException(status_code=404, detail="Student ID card not found")
        return card

    def list_all_cards(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[StudentIDCard], int]:
        q = self.db.query(StudentIDCard)
        total = q.count()
        offset = (page - 1) * page_size
        items = (
            q.order_by(StudentIDCard.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return items, total

    def _get_student_user_profile(self, *, student_id: str):
        return (
            self.db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .first()
        )

    def get_card_for_download(self, *, student_id: str, current_user) -> StudentIDCard:
        # Same rules as view
        return self.get_card_for_view(student_id=student_id, current_user=current_user)
