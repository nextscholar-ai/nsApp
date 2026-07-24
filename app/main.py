from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import DataError, IntegrityError, OperationalError, SQLAlchemyError

from app.api.config import settings
from app.api.database import SessionLocal
from app.core.exceptions import (
    AmbiguousIdentifierError,
    AuthenticationError,
    AuthorizationError,
    CapacityExceededError,
    DuplicateError,
    IdentifierNotFoundError,
    InvalidOperationError,
    NotFoundError,
    SchoolERPException,
    StudentNotEnrolledError,
    TeacherNotAssignedError,
    ValidationError,
)

# IMPORT MODELS (IMPORTANT)
from app.model import *  # noqa: F403
from app.routers.admin_router import router as admin_router
from app.routers.assignment_routers import router as assignment_router
from app.routers.attachment_router import router as attachment_router

# ROUTERS
from app.routers.auth_routers import router as auth_router
from app.routers.chat_routers import router as chat_router
from app.routers.daily_class_routers import router as daily_class_router
from app.routers.dashboard_routers import router as dashboard_router
from app.routers.exam_routers import router as exam_router
from app.routers.fees_routers import router as fees_router
from app.routers.ka_routers import router as ka_router
from app.routers.notice_routers import router as notice_router
from app.routers.promotion_routers import router as promotion_router
from app.routers.student_id_card_router import router as student_id_card_router
from app.routers.student_routers import router as student_router
from app.routers.student_search_router import router as student_search_router
from app.routers.study_material_routers import router as study_material_router
from app.routers.subject_routers import router as subject_router
from app.routers.teacher_router import router as teacher_router
from app.routers.teacher_search_router import router as teacher_search_router
from app.routers.timetable_routers import router as timetable_router
from app.routers.top_students_teachers_router import (
    router as top_students_teachers_router,
)
from app.routers.topic_routers import router as topic_router
from app.routers.unified_search_router import router as unified_search_router
from app.routers.zoom_routers import router as zoom_router

app = FastAPI(title="Student Activity Dashboard API")


# =========================
# GLOBAL EXCEPTION HANDLERS
# =========================


def _error_response(
    status_code: int,
    detail: str,
    error_type: str | None = None,
    extra: dict | None = None,
):
    content = {"detail": detail, "error": error_type or "unknown_error"}
    if extra:
        content.update(extra)
    return JSONResponse(status_code=status_code, content=content)


@app.exception_handler(AmbiguousIdentifierError)
async def ambiguous_identifier_handler(request: Request, exc: AmbiguousIdentifierError):
    return _error_response(
        status_code=409,
        detail=str(exc),
        error_type="ambiguous_identifier",
        extra={"candidates": exc.candidates},
    )


@app.exception_handler(IdentifierNotFoundError)
async def identifier_not_found_handler(request: Request, exc: IdentifierNotFoundError):
    return _error_response(404, detail=str(exc), error_type="identifier_not_found")


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    return _error_response(404, detail=str(exc), error_type="not_found")


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return _error_response(400, detail=str(exc), error_type="validation_error")


@app.exception_handler(DuplicateError)
async def duplicate_error_handler(request: Request, exc: DuplicateError):
    return _error_response(409, detail=str(exc), error_type="duplicate_entry")


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return _error_response(401, detail=str(exc), error_type="authentication_error")


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError):
    return _error_response(403, detail=str(exc), error_type="authorization_error")


@app.exception_handler(InvalidOperationError)
async def invalid_operation_handler(request: Request, exc: InvalidOperationError):
    return _error_response(400, detail=str(exc), error_type="invalid_operation")


@app.exception_handler(CapacityExceededError)
async def capacity_exceeded_handler(request: Request, exc: CapacityExceededError):
    return _error_response(400, detail=str(exc), error_type="capacity_exceeded")


@app.exception_handler(StudentNotEnrolledError)
async def student_not_enrolled_handler(request: Request, exc: StudentNotEnrolledError):
    return _error_response(400, detail=str(exc), error_type="student_not_enrolled")


@app.exception_handler(TeacherNotAssignedError)
async def teacher_not_assigned_handler(request: Request, exc: TeacherNotAssignedError):
    return _error_response(400, detail=str(exc), error_type="teacher_not_assigned")


@app.exception_handler(SchoolERPException)
async def base_school_erp_handler(request: Request, exc: SchoolERPException):
    return _error_response(500, detail=str(exc), error_type="internal_error")


# ---- SQLAlchemy / Database Errors ----


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    orig = getattr(exc, "orig", None)
    detail = (
        getattr(orig, "pgerror", None) or getattr(orig, "args", [None])[0] or str(exc)
    )
    return _error_response(
        409,
        detail=f"Database integrity error: {detail}",
        error_type="integrity_error",
    )


@app.exception_handler(DataError)
async def data_error_handler(request: Request, exc: DataError):
    return _error_response(
        400,
        detail=f"Invalid data: {exc!s}",
        error_type="data_error",
    )


@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    return _error_response(
        503,
        detail="Database unavailable",
        error_type="database_unavailable",
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    return _error_response(
        500,
        detail="A database error occurred",
        error_type="db_error",
    )


# ---- Catch-all for unhandled exceptions (never leak stack traces) ----


@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception):
    return _error_response(
        500,
        detail="An unexpected error occurred",
        error_type="internal_error",
    )


# =========================
# ROUTERS
# =========================

app.include_router(auth_router)
app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(subject_router)
app.include_router(daily_class_router)
app.include_router(assignment_router)
app.include_router(exam_router)
app.include_router(fees_router)

app.include_router(chat_router)
app.include_router(dashboard_router)

app.include_router(notice_router)
app.include_router(admin_router)
app.include_router(top_students_teachers_router)
app.include_router(study_material_router)

app.include_router(timetable_router)
app.include_router(student_id_card_router)
app.include_router(attachment_router)
app.include_router(student_search_router)
app.include_router(teacher_search_router)
app.include_router(unified_search_router)
app.include_router(zoom_router)
app.include_router(topic_router)
app.include_router(ka_router)
app.include_router(promotion_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path("uploads").mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# =========================
# STARTUP: ID CARD BACKFILL
# =========================
# Automatically generate ID cards for any student that is actively enrolled
# in the current academic session but doesn't have one yet (e.g. because
# they were admitted before their profile was fully filled in). Safe to
# run on every startup - existing cards are left untouched.


@app.on_event("startup")
def backfill_id_cards_on_startup() -> None:
    from app.services.student_id_card_service import StudentIDCardService

    db = SessionLocal()
    try:
        service = StudentIDCardService(db)
        service.backfill_missing_id_cards()
    except Exception:  # noqa: S110
        # Never let a backfill problem prevent the app from starting.
        pass
    finally:
        db.close()


# =========================
# STARTUP: REGISTRATION NUMBER BACKFILL
# =========================
# Assigns a registration_number to any pre-existing student that
# doesn't have one yet (new students get one at creation time, see
# admin_router.create_user). Cheap no-op on repeated runs - students
# that already have a registration_number are skipped.
#
# Note: there is no search-index backfill step here. Student/Teacher
# search (app/services/search) queries student_profiles/teacher_profiles
# directly on every request, so newly inserted or edited records are
# searchable immediately with nothing to (re)build on startup.


@app.on_event("startup")
def backfill_student_search_on_startup() -> None:
    from app.services.registration_number_service import RegistrationNumberService

    db = SessionLocal()
    try:
        RegistrationNumberService(
            db,
        ).backfill_missing_registration_numbers()
    except Exception:  # noqa: S110
        pass
    finally:
        db.close()


# =========================
# HEALTH CHECK
# =========================


@app.get("/")
def home():
    return {"status": "running", "message": "Student ERP Backend Active"}
