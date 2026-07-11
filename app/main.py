from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.database import Base, engine
from sqlalchemy import inspect, text

import os
from fastapi.staticfiles import StaticFiles

# IMPORT MODELS (IMPORTANT)
from app.model import *


# ROUTERS
from app.routers.auth_routers import router as auth_router
from app.routers.student_routers import router as student_router
from app.routers.teacher_router import router as teacher_router
from app.routers.subject_routers import router as subject_router
from app.routers.daily_class_routers import router as daily_class_router
from app.routers.assignment_routers import router as assignment_router
from app.routers.exam_routers import router as exam_router


from app.routers.fees_routers import router as fees_router
from app.routers.chat_routers import router as chat_router
from app.routers.dashboard_routers import router as dashboard_router

from app.routers.notice_routers import router as notice_router
from app.routers.admin_router import router as admin_router
from app.routers.top_students_teachers_router import router as top_students_teachers_router

from app.routers.study_material_routers import router as study_material_router

from app.routers.timetable_routers import router as timetable_router
from app.routers.student_id_card_router import router as student_id_card_router
from app.routers.attachment_router import router as attachment_router
from app.routers.student_search_router import router as student_search_router
from app.routers.teacher_search_router import router as teacher_search_router

from app.api.database import SessionLocal

# NOTE: Search (students/teachers by name or email) is implemented with
# pure Python similarity matching (RapidFuzz) directly against the live
# student_profiles/teacher_profiles tables - see app/helpers/search,
# app/repositories/search, app/services/search. No PostgreSQL extension,
# no vector column, and no embedding/cache table are used or required.

# CREATE TABLES
Base.metadata.create_all(bind=engine)



def ensure_missing_columns():
    inspector = inspect(engine)
    required_columns = {
        "academic_sessions": {
            "created_by": "INTEGER",
            "updated_by": "INTEGER",
        },
        "users": {
            "deleted_by": "INTEGER",
        },
        "admin_profiles": {
            "created_by": "INTEGER",
            "updated_by": "INTEGER",
        },
        "student_profiles": {
            "registration_number": "VARCHAR(30)",
        },
    }

    with engine.begin() as conn:
        for table_name, columns in required_columns.items():
            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }
            for column_name, column_type in columns.items():
                if column_name not in existing_columns:
                    conn.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )

        # registration_number needs to be unique (mirrors the model
        # definition) - added separately since it's an index, not a column.
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "ix_student_profiles_registration_number_unique "
                "ON student_profiles (registration_number) "
                "WHERE registration_number IS NOT NULL"
            )
        )


ensure_missing_columns()

app = FastAPI(
    title="Student Activity Dashboard API"
)


# =========================
# GLOBAL EXCEPTION HANDLERS
# =========================
# IdentifierResolverService (app/services/identifier_resolver_service.py)
# lets any endpoint accept a student/teacher's name or email instead of
# their raw id. These two handlers turn its exceptions into proper HTTP
# responses everywhere, without needing a try/except in every router.

from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AmbiguousIdentifierError, NotFoundError


@app.exception_handler(AmbiguousIdentifierError)
async def ambiguous_identifier_handler(request: Request, exc: AmbiguousIdentifierError):
    return JSONResponse(
        status_code=409,
        content={
            "detail": str(exc),
            "error": "ambiguous_identifier",
            "candidates": exc.candidates,
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


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

app.add_middleware(

    CORSMiddleware,
    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)

os.makedirs(
    "uploads",
    exist_ok=True
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


# =========================
# STARTUP: ID CARD BACKFILL
# =========================
# Automatically generate ID cards for any student that is actively enrolled
# in the current academic session but doesn't have one yet (e.g. because
# they were admitted before their profile was fully filled in). Safe to
# run on every startup - existing cards are left untouched.

@app.on_event("startup")
def backfill_id_cards_on_startup():
    from app.services.student_id_card_service import StudentIDCardService

    db = SessionLocal()
    try:
        service = StudentIDCardService(db)
        result = service.backfill_missing_id_cards()
        print(f"[startup] ID card backfill: {result}")
    except Exception as exc:
        # Never let a backfill problem prevent the app from starting.
        print(f"[startup] ID card backfill skipped due to error: {exc}")
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
def backfill_student_search_on_startup():
    from app.services.registration_number_service import RegistrationNumberService

    db = SessionLocal()
    try:
        reg_result = RegistrationNumberService(db).backfill_missing_registration_numbers()
        print(f"[startup] Registration number backfill: {reg_result}")
    except Exception as exc:
        print(f"[startup] Registration number backfill skipped due to error: {exc}")
    finally:
        db.close()


# =========================
# HEALTH CHECK
# =========================

@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Student ERP Backend Active"
    }
