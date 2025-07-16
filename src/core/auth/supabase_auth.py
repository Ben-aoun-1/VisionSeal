"""
Supabase Authentication Integration for VisionSeal
Uses Supabase Auth for user management, registration, and JWT tokens
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from supabase import Client
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from core.config.settings import settings
from core.database.supabase_client import supabase_manager
from core.logging.setup import get_logger

logger = get_logger("supabase_auth")
security = HTTPBearer()


class SupabaseAuthManager:
    """Manages authentication using Supabase Auth"""
    
    def __init__(self):
        self.supabase = supabase_manager.get_client(use_service_key=False)
        self.service_client = supabase_manager.get_client(use_service_key=True)
        
    async def register_user(self, email: str, password: str, user_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Register a new user with Supabase Auth"""
        try:
            # Prepare user metadata
            metadata = user_metadata or {}
            
            # Register with Supabase Auth
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata
                }
            })
            
            if response.user:
                logger.info(f"✅ User registered successfully: {email}")
                
                # Create user profile manually since trigger was removed
                await self._create_user_profile(response.user, metadata)
                
                return {
                    "success": True,
                    "user": response.user,
                    "message": "User registered successfully. Please check your email for verification."
                }
            else:
                logger.error(f"❌ Failed to register user: {email}")
                return {
                    "success": False,
                    "error": "Registration failed"
                }
                
        except Exception as e:
            logger.error(f"❌ Registration error: {str(e)}")
            # Check if it's a Supabase auth error
            if hasattr(e, 'message'):
                error_msg = e.message
            else:
                error_msg = str(e)
            
            # More specific error handling
            if "already registered" in error_msg.lower():
                raise HTTPException(status_code=400, detail="User already exists")
            elif "invalid email" in error_msg.lower():
                raise HTTPException(status_code=400, detail="Invalid email format")
            elif "weak password" in error_msg.lower():
                raise HTTPException(status_code=400, detail="Password too weak")
            else:
                raise HTTPException(status_code=400, detail=f"Registration failed: {error_msg}")
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with Supabase Auth"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                logger.info(f"✅ User logged in successfully: {email}")
                
                # Update last login
                await self._update_last_login(response.user.id)
                
                return {
                    "success": True,
                    "user": response.user,
                    "session": response.session,
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_in": response.session.expires_in
                }
            else:
                logger.warning(f"⚠️ Failed login attempt: {email}")
                return {
                    "success": False,
                    "error": "Invalid credentials"
                }
                
        except Exception as e:
            logger.error(f"❌ Login error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    
    async def logout_user(self, token: str) -> Dict[str, Any]:
        """Logout user and invalidate session"""
        try:
            # Validate token format
            if not token or len(token) < 20:
                raise HTTPException(status_code=400, detail="Invalid token format")
            
            # Get user info before logout for logging
            user_info = None
            try:
                user_response = self.supabase.auth.get_user(token)
                if user_response.user:
                    user_info = user_response.user.email
            except:
                pass  # User info is optional for logout
            
            # Set the session token and sign out
            self.supabase.auth.set_session(token, refresh_token=None)
            response = self.supabase.auth.sign_out()
            
            logger.info(f"✅ User logged out successfully: {user_info or 'unknown'}")
            return {
                "success": True,
                "message": "Logged out successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Logout error: {str(e)}")
            # Even if logout fails, return success to avoid client-side issues
            # The token will still expire naturally
            return {
                "success": True,
                "message": "Logged out successfully"
            }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh user session token"""
        try:
            # Validate refresh token format
            if not refresh_token or not isinstance(refresh_token, str):
                raise HTTPException(status_code=400, detail="Invalid refresh token format")
            
            # Attempt to refresh session
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if response.session and response.session.access_token:
                logger.info("✅ Token refreshed successfully")
                
                # Update last login for user
                if response.user:
                    await self._update_last_login(response.user.id)
                
                return {
                    "success": True,
                    "session": response.session,
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_in": response.session.expires_in,
                    "user": response.user
                }
            else:
                logger.warning("⚠️ Token refresh failed - invalid session response")
                return {
                    "success": False,
                    "error": "Invalid refresh token or session expired"
                }
                
        except Exception as e:
            logger.error(f"❌ Token refresh error: {str(e)}")
            # Distinguish between different error types
            if "invalid" in str(e).lower() or "expired" in str(e).lower():
                raise HTTPException(status_code=401, detail="Refresh token invalid or expired")
            else:
                raise HTTPException(status_code=500, detail="Token refresh service unavailable")
    
    async def verify_email(self, token: str) -> Dict[str, Any]:
        """Verify user email with token"""
        try:
            response = self.supabase.auth.verify_otp({
                "token": token,
                "type": "signup"
            })
            
            if response.user:
                logger.info(f"✅ Email verified successfully: {response.user.email}")
                
                # Update user profile verification status
                await self._update_verification_status(response.user.id, True)
                
                return {
                    "success": True,
                    "message": "Email verified successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid verification token"
                }
                
        except Exception as e:
            logger.error(f"❌ Email verification error: {str(e)}")
            raise HTTPException(status_code=400, detail="Email verification failed")
    
    async def reset_password(self, email: str) -> Dict[str, Any]:
        """Send password reset email"""
        try:
            response = self.supabase.auth.reset_password_email(email)
            
            logger.info(f"✅ Password reset email sent: {email}")
            return {
                "success": True,
                "message": "Password reset email sent"
            }
            
        except Exception as e:
            logger.error(f"❌ Password reset error: {str(e)}")
            raise HTTPException(status_code=400, detail="Password reset failed")
    
    async def update_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Update user password with reset token"""
        try:
            # Set the session token
            self.supabase.auth.set_session(token, refresh_token=None)
            
            # Update password
            response = self.supabase.auth.update_user({
                "password": new_password
            })
            
            if response.user:
                logger.info(f"✅ Password updated successfully: {response.user.email}")
                return {
                    "success": True,
                    "message": "Password updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Password update failed"
                }
                
        except Exception as e:
            logger.error(f"❌ Password update error: {str(e)}")
            raise HTTPException(status_code=400, detail="Password update failed")
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Get current user from JWT token"""
        try:
            if not credentials or not credentials.credentials:
                raise HTTPException(status_code=401, detail="Missing authentication token")
            
            token = credentials.credentials
            
            # Validate token format
            if not token or len(token) < 20:
                raise HTTPException(status_code=401, detail="Invalid token format")
            
            # Verify token with Supabase
            response = self.supabase.auth.get_user(token)
            
            if response.user:
                # Check if user is still active
                user_profile = await self._get_user_profile(response.user.id)
                
                # Verify user account is active
                if user_profile and user_profile.get("status") == "suspended":
                    raise HTTPException(status_code=403, detail="Account suspended")
                
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "email_verified": response.user.email_confirmed_at is not None,
                    "created_at": response.user.created_at,
                    "last_sign_in": response.user.last_sign_in_at,
                    "user_metadata": response.user.user_metadata,
                    "profile": user_profile,
                    "is_active": user_profile.get("status", "active") == "active" if user_profile else True
                }
            else:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
                
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            logger.error(f"❌ Get current user error: {str(e)}")
            # Distinguish between different error types
            if "expired" in str(e).lower():
                raise HTTPException(status_code=401, detail="Token expired")
            elif "invalid" in str(e).lower():
                raise HTTPException(status_code=401, detail="Invalid token")
            else:
                raise HTTPException(status_code=500, detail="Authentication service unavailable")
    
    async def _create_user_profile(self, user, metadata: Dict):
        """Create user profile in custom table"""
        try:
            profile_data = {
                "id": user.id,
                "email": user.email,
                "first_name": metadata.get("first_name", ""),
                "last_name": metadata.get("last_name", ""),
                "company": metadata.get("company"),
                "phone": metadata.get("phone"),
                "sector": metadata.get("sector"),
                "address": metadata.get("address"),
                "role": metadata.get("role", "user"),
                "status": "pending_verification",
                "preferences": metadata.get("preferences", {})
            }
            
            response = self.service_client.table('user_profiles').insert(profile_data).execute()
            logger.info(f"✅ User profile created: {user.email}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create user profile: {str(e)}")
            # Try to update existing profile if insert failed
            try:
                update_response = self.service_client.table('user_profiles').update(profile_data).eq('id', user.id).execute()
                logger.info(f"✅ User profile updated: {user.email}")
            except Exception as update_error:
                logger.error(f"❌ Failed to update user profile: {str(update_error)}")
                raise e
    
    async def _get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile from custom table"""
        try:
            response = self.service_client.table('user_profiles').select('*').eq('id', user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get user profile: {str(e)}")
            return None
    
    async def _update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        try:
            response = self.service_client.table('user_profiles').update({
                "last_login": datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            
        except Exception as e:
            logger.error(f"❌ Failed to update last login: {str(e)}")
    
    async def _update_verification_status(self, user_id: str, verified: bool):
        """Update user email verification status"""
        try:
            response = self.service_client.table('user_profiles').update({
                "is_verified": verified,
                "status": "active" if verified else "pending_verification"
            }).eq('id', user_id).execute()
            
        except Exception as e:
            logger.error(f"❌ Failed to update verification status: {str(e)}")


# Global auth manager instance
auth_manager = SupabaseAuthManager()


# Dependency for getting current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user"""
    return await auth_manager.get_current_user(credentials)


# Optional authentication (for endpoints that work with or without auth)
async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Optional authentication dependency"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.replace("Bearer ", "")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        return await auth_manager.get_current_user(credentials)
    except:
        return None