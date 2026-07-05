from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from app.api.database import SessionLocal,get_db


from app.model import (
    User,
    StudentProfile,
    TeacherProfile
)



from app.auth import verify_access_token

ROLE_ADMIN="admin"
ROLE_TEACHER="teacher"
ROLE_STUDENT="student"

# =====================================================
# JWT TOKEN
# =====================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token"
)


# =====================================================
# CURRENT USER
# =====================================================

def get_current_user(

    token: str = Depends(oauth2_scheme),

    db: Session = Depends(get_db)

):

    payload = verify_access_token(token)

    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(
        User.id == int(payload["sub"])
    ).first()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not user.is_active:

        raise HTTPException(
            status_code=403,
            detail="Account disabled"
        )

    return user



def _normalize_role(role):
    return getattr(role, "value", role)


def require_role(*roles):

    expected_roles = {_normalize_role(role) for role in roles}

    def checker(

        current_user: User = Depends(
            get_current_user
        )

    ):

        current_role = _normalize_role(current_user.role)

        if current_role not in expected_roles:

            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )

        return current_user

    return checker


# =====================================================
# CURRENT STUDENT PROFILE
# =====================================================

def get_current_student(

    current_user: User = Depends(
        require_role("student")
    ),

    db: Session = Depends(
        get_db
    )

):

    student = (

        db.query(StudentProfile)

        .filter(
            StudentProfile.user_id
            == current_user.id
        )

        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail=(
                "Student profile not found for current user. "
                f"current_user.id={current_user.id} "
                "(ensure profile row exists in student_profiles.user_id)"
            )
        )

    return student


# Alias: routers import this name expecting the student's profile object,
# which get_current_student already returns.
get_current_student_profile = get_current_student

def get_student_by_student_id(

    student_id: str,

    db: Session

):

    student = (

        db.query(StudentProfile)

        .filter(
            StudentProfile.student_id
            == student_id
        )

        .first()
    )

    if not student:

        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return student


# =====================================================
# CURRENT STUDENT ID
# =====================================================



def get_current_teacher(

    current_user: User = Depends(
        require_role("teacher")
    ),

    db: Session = Depends(get_db)
):

    teacher = (

        db.query(TeacherProfile)

        .filter(
            TeacherProfile.user_id
            == current_user.id
        )

        .first()
    )

    if not teacher:

        raise HTTPException(
            status_code=404,
            detail="Teacher profile not found"
        )

    return teacher


# Alias: routers import this name expecting the teacher's profile object,
# which get_current_teacher already returns.
get_current_teacher_profile = get_current_teacher


def get_current_admin(

    current_user: User = Depends(
        require_role("admin")
    )
):

    return current_user


# Alias: this project has a single ADMIN role (no separate super-admin
# distinction), so require_super_admin simply requires the admin role.
require_super_admin = get_current_admin



from app.model import Assignment


def verify_assignment_owner(
    assignment_id: int,
    current_user: User,
    db: Session
):

    assignment = (

        db.query(Assignment)

        .filter(
            Assignment.id == assignment_id,
            Assignment.is_active == True
        )

        .first()
    )

    if not assignment:

        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    if current_user.role == "admin":
        return assignment

    if assignment.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only manage your own assignments"
        )

    return assignment
