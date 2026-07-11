from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.model import User, TeacherProfile, StudentProfile, TeacherSubject, StudentClass, ClassRoom
from app.repositories.profile_repository import StudentProfileRepository, TeacherProfileRepository
from app.schemas.admin_student_teacher import (
    TeacherAdminListResponse,
    StudentAdminListResponse,
)


class AdminStudentTeacherService:
    def __init__(self, db: Session):
        self.db = db
        self.student_repo = StudentProfileRepository(db)
        self.teacher_repo = TeacherProfileRepository(db)

    def _paginate(self, page: int, page_size: int) -> Tuple[int, int]:
        offset = (page - 1) * page_size
        return offset, page_size

    def list_teachers_admin(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        department: Optional[str] = None,
        subject: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ):
        # Base query
        from app.model import User as UserModel, ClassRoom, TeacherProfile as TeacherProfileModel

        q = (
            self.db.query(
                UserModel.id.label("user_id"),
                TeacherProfileModel.teacher_id.label("teacher_id"),
                TeacherProfileModel.teacher_name.label("teacher_name"),
                UserModel.email.label("email"),
                UserModel.phone.label("phone"),
                TeacherProfileModel.designation.label("designation"),
                TeacherProfileModel.department.label("department"),
                # assigned_classes: distinct classroom display_name per teacher
                func.array_agg(func.distinct(ClassRoom.display_name)).label("assigned_classes"),
                TeacherProfileModel.is_active.label("status"),
            )
            .select_from(UserModel)
            .join(TeacherProfileModel, TeacherProfileModel.user_id == UserModel.id)
            .outerjoin(TeacherSubject, TeacherSubject.teacher_id == TeacherProfileModel.teacher_id)
            .outerjoin(ClassRoom, ClassRoom.id == TeacherSubject.classroom_id)
            .filter(UserModel.role == "teacher")
        )

        if search:
            s = search.strip()
            q = q.filter(
                func.lower(TeacherProfileModel.teacher_name).contains(func.lower(func.cast(s, func.text())))
                | TeacherProfileModel.teacher_id.contains(s)
                | UserModel.email.contains(s)
            )

        if is_active is not None:
            q = q.filter(TeacherProfileModel.is_active == is_active)

        if department:
            q = q.filter(TeacherProfileModel.department == department)

        q = q.group_by(
            UserModel.id,
            TeacherProfileModel.teacher_id,
            TeacherProfileModel.teacher_name,
            UserModel.email,
            UserModel.phone,
        )

        total = q.count()
        offset, limit = self._paginate(page, page_size)
        rows = q.order_by(TeacherProfileModel.teacher_name.asc()).offset(offset).limit(limit).all()

        data = []
        for r in rows:
            assigned = [c for c in r.assigned_classes if c is not None] if r.assigned_classes else []
            data.append(
                TeacherAdminListResponse(
                    user_id=r.user_id,
                    teacher_id=r.teacher_id,
                    teacher_name=r.teacher_name,
                    email=r.email,
                    phone=r.phone,
                    designation=r.designation,
                    department=r.department,
                    assigned_classes=list(assigned),
                    status=None,
                )
            )

        return {
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }

    def list_students_admin(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        class_id: Optional[int] = None,
        class_code: Optional[str] = None,
    ):
        from app.model import User as UserModel, ClassRoom, AcademicSession

        # We need one row per student, with their active class/section.
        # Using ACTIVE student_classes and selecting the one with latest admission_date as the "class".
        sc = StudentClass
        sp = StudentProfile
        u = UserModel
        cr = ClassRoom

        # Subquery to pick latest ACTIVE class per student
        # (kept for future improvements; currently not used in the mapping logic)
        latest_class_subq = (

            self.db.query(
                sc.student_id.label("student_id"),
                cr.class_name.label("class_name"),
                cr.section.label("section"),
                cr.display_name.label("display_name"),
            )
            .join(cr, cr.id == sc.classroom_id)
            .filter(sc.status == "ACTIVE")
        )

        # Apply filters to student-class selection
        if class_id is not None:
            latest_class_subq = latest_class_subq.filter(sc.classroom_id == class_id)

        if class_code is not None:
            latest_class_subq = latest_class_subq.filter(cr.class_code == class_code)

        if search:
            s = search.strip()
            latest_class_subq = latest_class_subq  # applied later on student/user fields

        # NOTE: to keep it simple and compatible across DBs, we fetch all matching students then map their latest class.
        # (Better SQL can be added later if needed.)

        students_q = (
            self.db.query(
                u.id.label("user_id"),
                sp.student_id.label("student_id"),
                sp.student_name.label("student_name"),
                u.email.label("email"),
                u.phone.label("phone"),
            )
            .select_from(u)
            .join(sp, sp.user_id == u.id)
            .filter(u.role == "student")
        )

        if search:
            s = search.strip()
            students_q = students_q.filter(
                sp.student_name.contains(s)
                | sp.student_id.contains(s)
                | u.email.contains(s)
                | u.phone.contains(s)
            )

        students_q = students_q.order_by(sp.student_name.asc())
        total = students_q.count()
        offset, limit = self._paginate(page, page_size)
        student_rows = students_q.offset(offset).limit(limit).all()

        # Fetch latest active class/section per student in the current page
        student_ids = [r.student_id for r in student_rows]
        class_map = {}
        if student_ids:
            class_rows = (
                self.db.query(sc.student_id, cr.class_name, cr.section)
                .join(cr, cr.id == sc.classroom_id)
                .filter(sc.student_id.in_(student_ids), sc.status == "ACTIVE")
            )

            if class_id is not None:
                class_rows = class_rows.filter(sc.classroom_id == class_id)
            if class_code is not None:
                class_rows = class_rows.filter(cr.class_code == class_code)

            class_rows = class_rows.order_by(sc.student_id.asc(), sc.admission_date.desc())
            seen = set()
            for rr in class_rows.all():
                sid = rr.student_id
                if sid in seen:
                    continue
                seen.add(sid)
                class_map[sid] = rr

        data = []
        for r in student_rows:
            cc = class_map.get(r.student_id)
            class_name = cc.class_name if cc else None
            section_name = cc.section if cc else None
            data.append(
                StudentAdminListResponse(
                    user_id=r.user_id,
                    student_id=r.student_id,
                    student_name=r.student_name,
                    class_=class_name,

                    section=section_name,
                    email=r.email,
                    phone=r.phone,
                    status=None,
                )
            )

        return {
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }

