"""
Session Management Middleware
Tracks user sessions and provides session-based security features
"""
import time
from typing import Dict, Optional, Set, List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
import json

from core.logging.setup import get_logger
from core.config.settings import settings

logger = get_logger("session_middleware")


class SessionManager:
    """Manages user sessions with security features"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self.session_timeout = 24 * 3600  # 24 hours in seconds
        self.max_sessions_per_user = 5
    
    def create_session(self, user_id: str, token: str, client_ip: str, user_agent: str) -> str:
        """Create a new session for a user"""
        session_id = f"session_{user_id}_{int(time.time())}"
        
        # Check max sessions per user
        if user_id in self.user_sessions:
            if len(self.user_sessions[user_id]) >= self.max_sessions_per_user:
                # Remove oldest session
                oldest_session = min(self.user_sessions[user_id], 
                                   key=lambda s: self.active_sessions.get(s, {}).get('created_at', 0))
                self.invalidate_session(oldest_session)
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'token_hash': hash(token),  # Store hash, not actual token
            'client_ip': client_ip,
            'user_agent': user_agent,
            'created_at': time.time(),
            'last_activity': time.time(),
            'request_count': 0,
            'is_active': True
        }
        
        self.active_sessions[session_id] = session_data
        
        # Track user sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)
        
        logger.info(f"Session created for user {user_id}: {session_id}")
        return session_id
    
    def update_session_activity(self, session_id: str, request_path: str = None):
        """Update session activity"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session['last_activity'] = time.time()
            session['request_count'] += 1
            
            if request_path:
                if 'recent_requests' not in session:
                    session['recent_requests'] = []
                session['recent_requests'].append({
                    'path': request_path,
                    'timestamp': time.time()
                })
                # Keep only last 10 requests
                session['recent_requests'] = session['recent_requests'][-10:]
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        return self.active_sessions.get(session_id)
    
    def validate_session(self, session_id: str, token: str, client_ip: str) -> bool:
        """Validate session with security checks"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        # Check if session is active
        if not session.get('is_active', False):
            return False
        
        # Check session timeout
        if time.time() - session['last_activity'] > self.session_timeout:
            self.invalidate_session(session_id)
            return False
        
        # Validate token hash
        if hash(token) != session['token_hash']:
            logger.warning(f"Token mismatch for session {session_id}")
            return False
        
        # Check IP consistency (optional - can be disabled for mobile users)
        if settings.security.get('enforce_ip_consistency', False):
            if client_ip != session['client_ip']:
                logger.warning(f"IP mismatch for session {session_id}: {client_ip} vs {session['client_ip']}")
                return False
        
        return True
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session['is_active'] = False
            user_id = session.get('user_id')
            
            # Remove from user sessions
            if user_id and user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            
            logger.info(f"Session invalidated: {session_id}")
    
    def invalidate_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id].copy():
                self.invalidate_session(session_id)
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if (current_time - session['last_activity'] > self.session_timeout or 
                not session.get('is_active', False)):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.invalidate_session(session_id)
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Get all active sessions for a user"""
        if user_id not in self.user_sessions:
            return []
        
        sessions = []
        for session_id in self.user_sessions[user_id]:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id].copy()
                # Remove sensitive data
                session.pop('token_hash', None)
                sessions.append(session)
        
        return sessions
    
    def get_session_stats(self) -> Dict:
        """Get session statistics"""
        active_count = len([s for s in self.active_sessions.values() if s.get('is_active', False)])
        total_users = len(self.user_sessions)
        
        return {
            'active_sessions': active_count,
            'total_sessions': len(self.active_sessions),
            'unique_users': total_users,
            'average_sessions_per_user': active_count / max(total_users, 1)
        }


class SessionMiddleware(BaseHTTPMiddleware):
    """Session management middleware"""
    
    def __init__(self, app, session_manager: SessionManager):
        super().__init__(app)
        self.session_manager = session_manager
    
    async def dispatch(self, request: Request, call_next):
        # Skip session tracking for health checks and static files
        skip_paths = ['/health', '/static', '/docs', '/openapi.json', '/redoc']
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Extract user info from token
        user_id = None
        session_id = None
        
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                if token and len(token) > 20:
                    from core.auth.supabase_auth import auth_manager
                    from fastapi.security import HTTPAuthorizationCredentials
                    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
                    user_info = await auth_manager.get_current_user(credentials)
                    user_id = user_info.get("user_id")
                    
                    # Get or create session
                    session_id = request.headers.get("X-Session-ID")
                    if not session_id:
                        # Create new session
                        client_ip = request.client.host if request.client else "unknown"
                        user_agent = request.headers.get("User-Agent", "unknown")
                        session_id = self.session_manager.create_session(
                            user_id, token, client_ip, user_agent
                        )
                    else:
                        # Validate existing session
                        client_ip = request.client.host if request.client else "unknown"
                        if not self.session_manager.validate_session(session_id, token, client_ip):
                            raise HTTPException(status_code=401, detail="Invalid session")
                    
                    # Update session activity
                    self.session_manager.update_session_activity(session_id, request.url.path)
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Session middleware error: {str(e)}")
            # Continue without session tracking on error
        
        # Add session info to request state
        request.state.user_id = user_id
        request.state.session_id = session_id
        
        # Process request
        response = await call_next(request)
        
        # Add session ID to response headers
        if session_id:
            response.headers["X-Session-ID"] = session_id
        
        return response


# Global session manager instance
session_manager = SessionManager()

# Background task to cleanup expired sessions
import asyncio
async def cleanup_sessions_task():
    """Background task to cleanup expired sessions"""
    while True:
        try:
            session_manager.cleanup_expired_sessions()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Session cleanup error: {str(e)}")
            await asyncio.sleep(60)  # Wait a minute on error

# Start cleanup task
try:
    asyncio.create_task(cleanup_sessions_task())
except:
    pass  # Ignore if event loop is not running