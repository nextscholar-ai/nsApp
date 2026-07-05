"""
Seed script: creates 10 ready-to-login accounts (4 admin, 3 teacher, 3 student)
directly in the database.

WHY THIS EXISTS
----------------
Account creation in this project is admin-only (POST /admin/user), which means
on a brand-new database there is no way to log in at all -- there's no
bootstrap admin. This script inserts the first batch of accounts directly via
SQLAlchemy so you can log in immediately. Once you have a couple of admin
accounts, use them (via /admin/user, /admin/student-profiles,
/admin/teacher-profiles, /admin/admin-profiles) to create everyone else.

USAGE
-----
    cd <project root>
    python3 scripts/seed_accounts.py

Run it again any time -- it skips accounts that already exist (matched by
email), so it's safe to re-run.

All seeded accounts use the password:  Password@123
(change it after first login)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.database import SessionLocal, engine, Base
from app.model import User, AdminProfile, TeacherProfile, StudentProfile
from app.core.enums import UserRole
from app.auth import hash_password
from app.helpers.code_generators import (
    generate_admin_id, generate_teacher_id, generate_student_id
)

DEFAULT_PASSWORD = "password123"

ACCOUNTS = [
    # ---- Admins (4) ----
    {"role": UserRole.ADMIN, "email": "ffaizan@student.iul.ac.in", "phone": "9517122461", "name": "Mohd Faizan", "super_admin": True},
    {"role": UserRole.ADMIN, "email": "admin2@school.test", "phone": "9000000002", "name": "Admin Two"},
    {"role": UserRole.ADMIN, "email": "admin3@school.test", "phone": "9000000003", "name": "Admin Three"},
    {"role": UserRole.ADMIN, "email": "admin4@school.test", "phone": "9000000004", "name": "Admin Four"},

    # ---- Teachers (3) ----
    {"role": UserRole.TEACHER, "email": "teacher1@school.test", "phone": "9000000011", "name": "Teacher One"},
    {"role": UserRole.TEACHER, "email": "teacher2@school.test", "phone": "9000000012", "name": "Teacher Two"},
    {"role": UserRole.TEACHER, "email": "teacher3@school.test", "phone": "9000000013", "name": "Teacher Three"},

    # ---- Students (3) ----
    {"role": UserRole.STUDENT, "email": "student1@school.test", "phone": "9000000021", "name": "Student One"},
    {"role": UserRole.STUDENT, "email": "student2@school.test", "phone": "9000000022", "name": "Student Two"},
    {"role": UserRole.STUDENT, "email": "student3@school.test", "phone": "9000000023", "name": "Student Three"},
]


def main():
    # Make sure all tables exist (no-op if they already do).
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    created, skipped = [], []

    try:
        for acc in ACCOUNTS:
            existing = db.query(User).filter(User.email == acc["email"]).first()
            if existing:
                skipped.append(acc["email"])
                continue

            user = User(
                email=acc["email"],
                phone=acc["phone"],
                role=acc["role"],
                password_hash=hash_password(DEFAULT_PASSWORD),
                email_verified=True,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            if acc["role"] == UserRole.ADMIN:
                user.admin_id = generate_admin_id(user.id)
                db.commit()
                db.refresh(user)

                db.add(AdminProfile(
                    admin_id=user.admin_id,
                    user_id=user.id,
                    admin_name=acc["name"],
                    can_create_admin=True,
                    super_admin=acc.get("super_admin", False),
                ))

            elif acc["role"] == UserRole.TEACHER:
                user.teacher_id = generate_teacher_id(user.id)
                db.commit()
                db.refresh(user)

                db.add(TeacherProfile(
                    teacher_id=user.teacher_id,
                    user_id=user.id,
                    teacher_name=acc["name"],
                ))

            elif acc["role"] == UserRole.STUDENT:
                user.student_id = generate_student_id(user.id)
                db.commit()
                db.refresh(user)

                db.add(StudentProfile(
                    student_id=user.student_id,
                    user_id=user.id,
                    student_name=acc["name"],
                    school_name="Default School",
                ))

            db.commit()
            created.append((acc["role"].value, acc["email"]))

    finally:
        db.close()

    print("\n=== Seed complete ===")
    if created:
        print(f"\nCreated {len(created)} account(s):")
        for role, email in created:
            print(f"  [{role:7}] {email}  /  password: {DEFAULT_PASSWORD}")
    if skipped:
        print(f"\nSkipped {len(skipped)} account(s) that already exist:")
        for email in skipped:
            print(f"  {email}")
    print(f"\nLogin at POST /auth/login with any of the emails above and password '{DEFAULT_PASSWORD}'.")
    print("Change these passwords after first login (POST /auth/change-password).")


if __name__ == "__main__":
    main()
