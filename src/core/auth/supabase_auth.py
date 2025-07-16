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
                
                # Create user profile in our custom table
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
            raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")
    
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
            # Set the session token
            self.supabase.auth.set_session(token, refresh_token=None)
            
            # Sign out
            response = self.supabase.auth.sign_out()
            
            logger.info("✅ User logged out successfully")
            return {
                "success": True,
                "message": "Logged out successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Logout error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh user session token"""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if response.session:
                logger.info("✅ Token refreshed successfully")
                return {
                    "success": True,
                    "session": response.session,
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_in": response.session.expires_in
                }
            else:
                logger.warning("⚠️ Token refresh failed")
                return {
                    "success": False,
                    "error": "Token refresh failed"
                }
                
        except Exception as e:
            logger.error(f"❌ Token refresh error: {str(e)}")
            raise HTTPException(status_code=401, detail="Token refresh failed")
    
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
            token = credentials.credentials
            
            # Verify token with Supabase
            response = self.supabase.auth.get_user(token)
            
            if response.user:
                # Get additional user profile data
                user_profile = await self._get_user_profile(response.user.id)
                
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "email_verified": response.user.email_confirmed_at is not None,
                    "created_at": response.user.created_at,
                    "last_sign_in": response.user.last_sign_in_at,
                    "user_metadata": response.user.user_metadata,
                    "profile": user_profile
                }
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
                
        except Exception as e:
            logger.error(f"❌ Get current user error: {str(e)}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
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
                "country": metadata.get("country"),
                "role": metadata.get("role", "user"),
                "status": "pending_verification",
                "created_at": datetime.utcnow().isoformat(),
                "preferences": metadata.get("preferences", {})
            }
            
            response = self.service_client.table('user_profiles').insert(profile_data).execute()
            logger.info(f"✅ User profile created: {user.email}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create user profile: {str(e)}")
    
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
                "last_login": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            
        except Exception as e:
            logger.error(f"❌ Failed to update last login: {str(e)}")
    
    async def _update_verification_status(self, user_id: str, verified: bool):
        """Update user email verification status"""
        try:
            response = self.service_client.table('user_profiles').update({
                "is_verified": verified,
                "status": "active" if verified else "pending_verification",
                "updated_at": datetime.utcnow().isoformat()
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