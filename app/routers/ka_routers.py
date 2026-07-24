from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import get_current_user, require_role
from app.model import KaCourse, KaStudent, StudentReport, User
from app.schemas.ka import (
    KaCourseCreate,
    KaCourseResponse,
    KaStudentCreate,
    KaStudentResponse,
    StudentReportCreate,
    StudentReportResponse,
)

router = APIRouter(prefix="/ka", tags=["Khan Academy"])

# ==================== KA COURSES ====================


@router.get("/courses", response_model=list[KaCourseResponse])
async def list_ka_courses(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return db.query(KaCourse).order_by(KaCourse.course_name).all()


@router.get("/courses/{id}", response_model=KaCourseResponse)
async def get_ka_course(
    id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    course = db.query(KaCourse).filter(KaCourse.ka_course_code == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/courses", response_model=KaCourseResponse, status_code=201)
async def create_ka_course(
    data: KaCourseCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    existing = db.query(KaCourse).filter(KaCourse.course_id == data.course_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Course with this ID already exists",
        )
    course = KaCourse(**data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.put("/courses/{id}", response_model=KaCourseResponse)
async def update_ka_course(
    id: str,
    data: KaCourseCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    course = db.query(KaCourse).filter(KaCourse.ka_course_code == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(course, key, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/courses/{id}")
async def delete_ka_course(
    id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    course = db.query(KaCourse).filter(KaCourse.ka_course_code == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"success": True, "message": "Course deleted"}


# ==================== KA STUDENTS ====================


@router.get("/students", response_model=list[KaStudentResponse])
async def list_ka_students(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return db.query(KaStudent).order_by(KaStudent.student_name).all()


@router.get("/students/{id}", response_model=KaStudentResponse)
async def get_ka_student(
    id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    student = db.query(KaStudent).filter(KaStudent.ka_student_code == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found in KA")
    return student


@router.post("/students", response_model=KaStudentResponse, status_code=201)
async def create_ka_student(
    data: KaStudentCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    student = KaStudent(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.put("/students/{id}", response_model=KaStudentResponse)
async def update_ka_student(
    id: str,
    data: KaStudentCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    student = db.query(KaStudent).filter(KaStudent.ka_student_code == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found in KA")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/students/{id}")
async def delete_ka_student(
    id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    student = db.query(KaStudent).filter(KaStudent.ka_student_code == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found in KA")
    db.delete(student)
    db.commit()
    return {"success": True, "message": "KA student deleted"}


# ==================== STUDENT REPORTS ====================


@router.get("/reports", response_model=list[StudentReportResponse])
async def list_student_reports(
    student_id: str | None = None,
    report_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(StudentReport)
    if student_id:
        query = query.filter(StudentReport.student_id == student_id)
    if report_type:
        query = query.filter(StudentReport.report_type == report_type)
    return query.order_by(StudentReport.created_at.desc()).all()


@router.get("/reports/{id}", response_model=StudentReportResponse)
async def get_student_report(
    id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    report = db.query(StudentReport).filter(StudentReport.report_code == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Student report not found")
    return report


@router.post("/reports", response_model=StudentReportResponse, status_code=201)
async def create_student_report(
    data: StudentReportCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    report = StudentReport(**data.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.put("/reports/{id}", response_model=StudentReportResponse)
async def update_student_report(
    id: str,
    data: StudentReportCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    report = db.query(StudentReport).filter(StudentReport.report_code == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Student report not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(report, key, value)
    db.commit()
    db.refresh(report)
    return report


@router.delete("/reports/{id}")
async def delete_student_report(
    id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    report = db.query(StudentReport).filter(StudentReport.report_code == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Student report not found")
    db.delete(report)
    db.commit()
    return {"success": True, "message": "Student report deleted"}
