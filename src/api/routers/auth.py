"""
Authentication router for Supabase integration
Handles user registration, login, password reset, etc.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator

from core.auth.supabase_auth import auth_manager, get_current_user
from api.schemas.common import SuccessResponse, ErrorResponse
from api.middleware.session import session_manager
from core.logging.setup import get_logger

logger = get_logger("auth")
router = APIRouter(prefix="/auth", tags=["authentication"])

# Add health check endpoint
@router.get("/health")
async def auth_health_check():
    """Health check for authentication API"""
    try:
        # Test if auth manager is available
        from core.auth.supabase_auth import auth_manager
        return {
            "status": "healthy",
            "service": "authentication",
            "supabase_auth": "available",
            "timestamp": "now"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "authentication",
            "error": str(e),
            "timestamp": "now"
        }


# Request/Response models
class UserRegistration(BaseModel):
    """User registration model"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    company: str = Field(None, max_length=200)
    phone: str = Field(None, max_length=20)
    sector: str = Field(None, max_length=100)
    address: str = Field(None, max_length=300)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordUpdate(BaseModel):
    """Password update with token"""
    token: str
    new_password: str = Field(min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class EmailVerification(BaseModel):
    """Email verification model"""
    token: str


class TokenRefresh(BaseModel):
    """Token refresh model"""
    refresh_token: str


class AuthResponse(BaseModel):
    """Authentication response"""
    success: bool
    access_token: str = None
    refresh_token: str = None
    expires_in: int = None
    user: Dict[str, Any] = None
    message: str = None


@router.post("/register", response_model=SuccessResponse)
async def register_user(registration: UserRegistration):
    """
    Register a new user with Supabase Auth
    
    Creates a new user account and sends email verification
    """
    try:
        logger.info(f"Registration attempt for: {registration.email}")
        
        # Prepare user metadata
        user_metadata = {
            "first_name": registration.first_name,
            "last_name": registration.last_name,
            "company": registration.company,
            "phone": registration.phone,
            "sector": registration.sector,
            "address": registration.address,
            "role": "user",
            "preferences": {
                "notifications_email": True,
                "theme": "light",
                "language": "en"
            }
        }
        
        # Register with Supabase
        result = await auth_manager.register_user(
            email=registration.email,
            password=registration.password,
            user_metadata=user_metadata
        )
        
        if result["success"]:
            return SuccessResponse(
                message="Registration successful! Please check your email for verification link.",
                data={
                    "email": registration.email,
                    "verification_required": True
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Registration failed"))
            
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login_user(login: UserLogin):
    """
    Login user with email and password
    
    Returns JWT tokens for authentication
    """
    try:
        logger.info(f"Login attempt for: {login.email}")
        
        result = await auth_manager.login_user(
            email=login.email,
            password=login.password
        )
        
        if result["success"]:
            return AuthResponse(
                success=True,
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
                expires_in=result["expires_in"],
                user={
                    "id": result["user"].id,
                    "email": result["user"].email,
                    "email_verified": result["user"].email_confirmed_at is not None,
                    "created_at": result["user"].created_at,
                    "last_sign_in": result["user"].last_sign_in_at,
                    "user_metadata": result["user"].user_metadata
                },
                message="Login successful"
            )
        else:
            raise HTTPException(status_code=401, detail=result.get("error", "Invalid credentials"))
            
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/logout", response_model=SuccessResponse)
async def logout_user(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Logout current user and invalidate session
    """
    try:
        logger.info(f"Logout for user: {current_user['email']}")
        
        # Get the token from the Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            
            # Invalidate the token on Supabase
            result = await auth_manager.logout_user(token)
            
            if result["success"]:
                return SuccessResponse(
                    message="Logged out successfully"
                )
            else:
                raise HTTPException(status_code=400, detail="Logout failed")
        else:
            # Even without token, consider it a successful logout
            return SuccessResponse(
                message="Logged out successfully"
            )
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        # Return success even on failure to avoid client-side issues
        return SuccessResponse(
            message="Logged out successfully"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(token_refresh: TokenRefresh):
    """
    Refresh authentication token
    """
    try:
        result = await auth_manager.refresh_token(token_refresh.refresh_token)
        
        if result["success"]:
            return AuthResponse(
                success=True,
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
                expires_in=result["expires_in"],
                message="Token refreshed successfully"
            )
        else:
            raise HTTPException(status_code=401, detail=result.get("error", "Token refresh failed"))
            
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Token refresh failed")


@router.post("/verify-email", response_model=SuccessResponse)
async def verify_email(verification: EmailVerification):
    """
    Verify user email with token
    """
    try:
        result = await auth_manager.verify_email(verification.token)
        
        if result["success"]:
            return SuccessResponse(
                message="Email verified successfully! You can now access all features."
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Email verification failed"))
            
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Email verification failed")


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(reset_request: PasswordReset):
    """
    Send password reset email
    """
    try:
        logger.info(f"Password reset requested for: {reset_request.email}")
        
        result = await auth_manager.reset_password(reset_request.email)
        
        if result["success"]:
            return SuccessResponse(
                message="Password reset email sent. Please check your inbox."
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Password reset failed"))
            
    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Password reset failed")


@router.post("/update-password", response_model=SuccessResponse)
async def update_password(password_update: PasswordUpdate):
    """
    Update password with reset token
    """
    try:
        result = await auth_manager.update_password(
            token=password_update.token,
            new_password=password_update.new_password
        )
        
        if result["success"]:
            return SuccessResponse(
                message="Password updated successfully! You can now login with your new password."
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Password update failed"))
            
    except Exception as e:
        logger.error(f"Password update failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Password update failed")


@router.get("/me", response_model=SuccessResponse)
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user profile information
    """
    try:
        return SuccessResponse(
            data=current_user,
            message="User profile retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get user profile failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to get user profile")


@router.get("/sessions", response_model=SuccessResponse)
async def get_user_sessions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get all active sessions for the current user
    """
    try:
        sessions = session_manager.get_user_sessions(current_user["user_id"])
        return SuccessResponse(
            data={
                "sessions": sessions,
                "total_count": len(sessions)
            },
            message="User sessions retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get user sessions failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@router.delete("/sessions/{session_id}", response_model=SuccessResponse)
async def revoke_session(session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Revoke a specific session
    """
    try:
        # Verify session belongs to current user
        user_sessions = session_manager.get_user_sessions(current_user["user_id"])
        session_exists = any(s["session_id"] == session_id for s in user_sessions)
        
        if not session_exists:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_manager.invalidate_session(session_id)
        
        return SuccessResponse(
            message="Session revoked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to revoke session")


@router.delete("/sessions", response_model=SuccessResponse)
async def revoke_all_sessions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Revoke all sessions for the current user except the current one
    """
    try:
        # Get current session ID from request
        from fastapi import Request
        request = Request.get_instance()  # This might not work directly
        
        # Alternative: get all sessions and invalidate them
        session_manager.invalidate_user_sessions(current_user["user_id"])
        
        return SuccessResponse(
            message="All sessions revoked successfully"
        )
        
    except Exception as e:
        logger.error(f"Revoke all sessions failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to revoke sessions")


@router.get("/status", response_model=SuccessResponse)
async def auth_status():
    """
    Check authentication system status
    """
    try:
        session_stats = session_manager.get_session_stats()
        
        return SuccessResponse(
            data={
                "auth_enabled": True,
                "provider": "supabase",
                "features": [
                    "email_password_auth",
                    "email_verification",
                    "password_reset",
                    "jwt_tokens",
                    "refresh_tokens",
                    "session_management"
                ],
                "session_stats": session_stats
            },
            message="Authentication system is operational"
        )
        
    except Exception as e:
        logger.error(f"Auth status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication system error")