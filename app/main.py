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
from app.routers.study_material_routers import router as study_material_router
from app.routers.timetable_routers import router as timetable_router

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


ensure_missing_columns()

app = FastAPI(
    title="Student Activity Dashboard API"
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
app.include_router(study_material_router)
app.include_router(timetable_router)

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
# HEALTH CHECK
# =========================

@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Student ERP Backend Active"
    }
