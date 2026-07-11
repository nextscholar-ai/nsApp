# ============================================================
# routers/auth_routers.py - Production Ready Authentication
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.api.config import settings
from app.api.database import get_db
from app.model import User, StudentProfile, TeacherProfile, AdminProfile
from app.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    ResendOTPRequest,
    UserResponse,
    ResponseSchema
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    verify_access_token,
    create_reset_token,
    verify_reset_token,
    generate_otp,
    create_auth_tokens
)
from app.dependencies import get_current_user, require_role
from app.core.enums import UserRole
from app.email_services import send_reset_email, send_otp_email, send_verification_email

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def authenticate_user(db: Session, identifier: str, password: str) -> User:
    """
    Authenticate user by email or phone.
    """
    user = db.query(User).filter(
        or_(
            User.email == identifier.lower().strip(),
            User.phone == identifier.strip()
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(password, user.password_hash):
        user.failed_login_count += 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deleted"
        )
    
    # Reset failed login count on successful login
    user.failed_login_count = 0
    user.last_login = datetime.utcnow()
    user.login_count += 1
    db.commit()
    db.refresh(user)
    
    return user

def get_user_profile(db: Session, user: User):
    """
    Get user's profile based on role.
    """
    profile_data = {
        "user": UserResponse.model_validate(user)
    }
    
    if user.role == UserRole.STUDENT:
        profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == user.id
        ).first()
        if profile:
            profile_data["profile"] = {
                "student_id": profile.student_id,
                "student_name": profile.student_name,
                "admission_number": profile.admission_number,
                "profile_photo": profile.profile_photo
            }
    
    elif user.role == UserRole.TEACHER:
        profile = db.query(TeacherProfile).filter(
            TeacherProfile.user_id == user.id
        ).first()
        if profile:
            profile_data["profile"] = {
                "teacher_id": profile.teacher_id,
                "teacher_name": profile.teacher_name,
                "designation": profile.designation,
                "employee_code": profile.employee_code,
                "profile_photo": profile.profile_photo
            }
    
    elif user.role == UserRole.ADMIN:
        profile = db.query(AdminProfile).filter(
            AdminProfile.user_id == user.id
        ).first()
        if profile:
            profile_data["profile"] = {
                "admin_id": profile.admin_id,
                "admin_name": profile.admin_name,
                "designation": profile.designation,
                "profile_photo": profile.profile_photo,
                "super_admin": profile.super_admin
            }
    
    return profile_data

# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    - **email**: User's email address
    - **password**: User's password
    """
    try:
        user = authenticate_user(db, request.email, request.password)
        
        # Create tokens
        tokens = create_auth_tokens(
            user_id=user.id,
            role=user.role.value
        )
        
        # Get profile data
        profile_data = get_user_profile(db, user)
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "expires_in": 3600,
            "user": UserResponse.model_validate(user),
            "profile": profile_data.get("profile")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )

@router.post("/token", include_in_schema=False)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token endpoint for Swagger UI.
    """
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        
        tokens = create_auth_tokens(
            user_id=user.id,
            role=user.role.value
        )
        
        return {
            "access_token": tokens["access_token"],
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": tokens["refresh_token"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2 login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        payload = verify_refresh_token(request.refresh_token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        user = db.query(User).filter(User.id == int(user_id)).first()

        if not user or not user.is_active or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        new_access_token = create_access_token({
            "sub": str(user.id),
            "role": user.role.value
        })

        return {
            "access_token": new_access_token,
            "refresh_token": request.refresh_token,
            "token_type": "bearer",
            "expires_in": 3600
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Refresh token error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while refreshing token: {type(e).__name__}: {str(e)}"
        )

@router.post("/logout", response_model=ResponseSchema)
async def logout(
    request: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user - clear device token and session.
    """
    try:
        if request.device_token and current_user.device_token == request.device_token:
            current_user.device_token = None
            db.commit()
        
        # If all_devices is True, clear all device tokens for this user
        if request.all_devices:
            current_user.device_token = None
            db.commit()
        
        return {
            "success": True,
            "message": "Logged out successfully",
            "data": None
        }
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )

# ============================================================
# PASSWORD MANAGEMENT
# ============================================================

@router.post("/change-password", response_model=ResponseSchema)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    """
    try:
        # Verify current password
        if not verify_password(request.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash and save new password
        current_user.password_hash = hash_password(request.new_password)
        current_user.password_changed_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Password changed successfully",
            "data": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing password"
        )

@router.post("/forgot-password", response_model=ResponseSchema)
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Request password reset - sends reset link to email.
    """
    try:
        user = db.query(User).filter(
            User.email == request.email.lower().strip()
        ).first()
        
        # Always return success to prevent email enumeration
        if not user:
            return {
                "success": True,
                "message": "If email exists, reset link will be sent",
                "data": None
            }
        
        # Generate reset token
        reset_token = create_reset_token(request.email)
        
        # Send reset email in background
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        background_tasks.add_task(
            send_reset_email,
            email=request.email,
            link=reset_link
        )
        
        return {
            "success": True,
            "message": "Password reset link sent to your email",
            "data": None
        }
        
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )

@router.post("/reset-password", response_model=ResponseSchema)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using token.
    """
    try:
        email = verify_reset_token(request.token)
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.password_hash = hash_password(request.new_password)
        user.password_changed_at = datetime.utcnow()
        user.last_password_reset = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Password reset successfully",
            "data": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting password"
        )

# ============================================================
# EMAIL VERIFICATION
# ============================================================

@router.post("/send-verification-otp", response_model=ResponseSchema)
async def send_verification_otp(
    request: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send verification OTP to email.
    """
    try:
        user = db.query(User).filter(
            User.email == request.email.lower().strip()
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Generate OTP
        otp = generate_otp(6)
        user.email_otp = otp
        user.email_otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.commit()
        
        # Send OTP email in background
        background_tasks.add_task(
            send_otp_email,
            email=user.email,
            otp=otp,
            purpose="email_verification"
        )
        
        return {
            "success": True,
            "message": "OTP sent successfully",
            "data": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send verification OTP error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending OTP"
        )

@router.post("/verify-email", response_model=ResponseSchema)
async def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email with OTP.
    """
    try:
        user = db.query(User).filter(
            User.email == request.email.lower().strip()
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Check OTP
        if not user.email_otp or user.email_otp != request.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP"
            )
        
        # Check expiry
        if user.email_otp_expiry and user.email_otp_expiry < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired"
            )
        
        user.email_verified = True
        user.email_otp = None
        user.email_otp_expiry = None
        db.commit()
        
        return {
            "success": True,
            "message": "Email verified successfully",
            "data": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify email error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying email"
        )

@router.post("/resend-otp", response_model=ResponseSchema)
async def resend_otp(
    request: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Resend verification OTP.
    """
    return await send_verification_otp(request, background_tasks, db)

# ============================================================
# OTP LOGIN (Alternative Login Method)
# ============================================================

@router.post("/send-login-otp", response_model=ResponseSchema)
async def send_login_otp(
    request: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send login OTP to email.
    """
    try:
        user = db.query(User).filter(
            User.email == request.email.lower().strip()
        ).first()
        
        if not user:
            # Return success to prevent email enumeration
            return {
                "success": True,
                "message": "If email exists, OTP will be sent",
                "data": None
            }
        
        # Generate OTP
        otp = generate_otp(6)
        user.email_otp = otp
        user.email_otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.commit()
        
        # Send OTP email in background
        background_tasks.add_task(
            send_otp_email,
            email=user.email,
            otp=otp,
            purpose="login"
        )
        
        return {
            "success": True,
            "message": "OTP sent successfully",
            "data": None
        }
        
    except Exception as e:
        logger.error(f"Send login OTP error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending OTP"
        )

@router.post("/verify-login-otp", response_model=LoginResponse)
async def verify_login_otp(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify login OTP and get access token.
    """
    try:
        user = db.query(User).filter(
            User.email == request.email.lower().strip()
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check OTP
        if not user.email_otp or user.email_otp != request.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP"
            )
        
        # Check expiry
        if user.email_otp_expiry and user.email_otp_expiry < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired"
            )
        
        # Clear OTP
        user.email_otp = None
        user.email_otp_expiry = None
        user.last_login = datetime.utcnow()
        user.login_count += 1
        db.commit()
        
        # Create tokens
        tokens = create_auth_tokens(
            user_id=user.id,
            role=user.role.value
        )
        
        # Get profile data
        profile_data = get_user_profile(db, user)
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "expires_in": 3600,
            "user": UserResponse.model_validate(user),
            "profile": profile_data.get("profile")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify login OTP error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during OTP verification"
        )

# ============================================================
# TOKEN VALIDATION
# ============================================================

@router.get("/validate-token", response_model=ResponseSchema)
async def validate_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate current access token and return user info.
    """
    try:
        profile_data = get_user_profile(db, current_user)
        
        return {
            "success": True,
            "message": "Token is valid",
            "data": {
                "user": UserResponse.model_validate(current_user),
                "profile": profile_data.get("profile")
            }
        }
        
    except Exception as e:
        logger.error(f"Validate token error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while validating token"
        )

# ============================================================
# HEALTH CHECK
# ============================================================

@router.get("/health")
async def auth_health_check():
    """
    Authentication service health check.
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat()
    }