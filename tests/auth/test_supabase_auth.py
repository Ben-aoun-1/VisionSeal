"""
Tests for Supabase authentication
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core.auth.supabase_auth import SupabaseAuthManager, get_current_user


class TestSupabaseAuthManager:
    """Test Supabase authentication manager"""

    @pytest.fixture
    def auth_manager(self, mock_supabase_client):
        """Create auth manager with mocked Supabase client"""
        with patch('core.auth.supabase_auth.supabase_manager') as mock_manager:
            mock_manager.get_client.return_value = mock_supabase_client
            manager = SupabaseAuthManager()
            return manager

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_manager, mock_supabase_client):
        """Test successful user registration"""
        # Mock successful registration response
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        
        mock_supabase_client.auth.sign_up.return_value = Mock(user=mock_user)
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = Mock()
        
        result = await auth_manager.register_user(
            email="test@example.com",
            password="SecurePass123!",
            user_metadata={"first_name": "Test", "last_name": "User"}
        )
        
        assert result["success"] is True
        assert result["user"] == mock_user
        assert "successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_register_user_failure(self, auth_manager, mock_supabase_client):
        """Test user registration failure"""
        # Mock failed registration response
        mock_supabase_client.auth.sign_up.return_value = Mock(user=None)
        
        result = await auth_manager.register_user(
            email="test@example.com",
            password="SecurePass123!"
        )
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_register_user_exception(self, auth_manager, mock_supabase_client):
        """Test user registration with exception"""
        # Mock exception during registration
        mock_supabase_client.auth.sign_up.side_effect = Exception("Registration failed")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.register_user(
                email="test@example.com",
                password="SecurePass123!"
            )
        
        assert exc_info.value.status_code == 400
        assert "Registration failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_user_success(self, auth_manager, mock_supabase_client):
        """Test successful user login"""
        # Mock successful login response
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        
        mock_session = Mock()
        mock_session.access_token = "access-token-123"
        mock_session.refresh_token = "refresh-token-123"
        mock_session.expires_in = 3600
        
        mock_supabase_client.auth.sign_in_with_password.return_value = Mock(
            user=mock_user,
            session=mock_session
        )
        
        # Mock profile update
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        result = await auth_manager.login_user(
            email="test@example.com",
            password="SecurePass123!"
        )
        
        assert result["success"] is True
        assert result["user"] == mock_user
        assert result["access_token"] == "access-token-123"
        assert result["refresh_token"] == "refresh-token-123"
        assert result["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_login_user_failure(self, auth_manager, mock_supabase_client):
        """Test user login failure"""
        # Mock failed login response
        mock_supabase_client.auth.sign_in_with_password.return_value = Mock(
            user=None,
            session=None
        )
        
        result = await auth_manager.login_user(
            email="test@example.com",
            password="wrongpassword"
        )
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_login_user_exception(self, auth_manager, mock_supabase_client):
        """Test user login with exception"""
        # Mock exception during login
        mock_supabase_client.auth.sign_in_with_password.side_effect = Exception("Login failed")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.login_user(
                email="test@example.com",
                password="SecurePass123!"
            )
        
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_logout_user_success(self, auth_manager, mock_supabase_client):
        """Test successful user logout"""
        # Mock successful logout
        mock_supabase_client.auth.set_session.return_value = None
        mock_supabase_client.auth.sign_out.return_value = Mock()
        
        result = await auth_manager.logout_user("valid-token")
        
        assert result["success"] is True
        assert "successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_logout_user_invalid_token(self, auth_manager, mock_supabase_client):
        """Test logout with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.logout_user("invalid")
        
        assert exc_info.value.status_code == 400
        assert "Invalid token format" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_logout_user_exception(self, auth_manager, mock_supabase_client):
        """Test logout with exception"""
        # Mock exception during logout
        mock_supabase_client.auth.sign_out.side_effect = Exception("Logout failed")
        
        # Should still return success (graceful degradation)
        result = await auth_manager.logout_user("valid-token-123")
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_manager, mock_supabase_client):
        """Test successful token refresh"""
        # Mock successful token refresh
        mock_user = Mock()
        mock_user.id = "user-123"
        
        mock_session = Mock()
        mock_session.access_token = "new-access-token"
        mock_session.refresh_token = "new-refresh-token"
        mock_session.expires_in = 3600
        
        mock_supabase_client.auth.refresh_session.return_value = Mock(
            session=mock_session,
            user=mock_user
        )
        
        # Mock profile update
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        result = await auth_manager.refresh_token("valid-refresh-token")
        
        assert result["success"] is True
        assert result["access_token"] == "new-access-token"
        assert result["refresh_token"] == "new-refresh-token"
        assert result["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_manager, mock_supabase_client):
        """Test token refresh with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.refresh_token("invalid")
        
        assert exc_info.value.status_code == 400
        assert "Invalid refresh token format" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_token_failure(self, auth_manager, mock_supabase_client):
        """Test token refresh failure"""
        # Mock failed refresh response
        mock_supabase_client.auth.refresh_session.return_value = Mock(session=None)
        
        result = await auth_manager.refresh_token("valid-refresh-token-123")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_refresh_token_exception(self, auth_manager, mock_supabase_client):
        """Test token refresh with exception"""
        # Mock exception during refresh
        mock_supabase_client.auth.refresh_session.side_effect = Exception("Token expired")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.refresh_token("valid-refresh-token-123")
        
        assert exc_info.value.status_code == 401
        assert "Refresh token invalid or expired" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, auth_manager, mock_supabase_client):
        """Test successful current user retrieval"""
        # Mock successful user retrieval
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.email_confirmed_at = "2024-01-01T00:00:00Z"
        mock_user.created_at = "2024-01-01T00:00:00Z"
        mock_user.last_sign_in_at = "2024-01-01T00:00:00Z"
        mock_user.user_metadata = {"first_name": "Test"}
        
        mock_supabase_client.auth.get_user.return_value = Mock(user=mock_user)
        
        # Mock profile retrieval
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"status": "active", "first_name": "Test"}]
        )
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token-123")
        
        result = await auth_manager.get_current_user(credentials)
        
        assert result["user_id"] == "user-123"
        assert result["email"] == "test@example.com"
        assert result["email_verified"] is True
        assert result["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self, auth_manager):
        """Test current user retrieval with no credentials"""
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.get_current_user(None)
        
        assert exc_info.value.status_code == 401
        assert "Missing authentication token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, auth_manager, mock_supabase_client):
        """Test current user retrieval with invalid token"""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token format" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_suspended_account(self, auth_manager, mock_supabase_client):
        """Test current user retrieval with suspended account"""
        # Mock user retrieval
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.email_confirmed_at = "2024-01-01T00:00:00Z"
        mock_user.created_at = "2024-01-01T00:00:00Z"
        mock_user.last_sign_in_at = "2024-01-01T00:00:00Z"
        mock_user.user_metadata = {}
        
        mock_supabase_client.auth.get_user.return_value = Mock(user=mock_user)
        
        # Mock suspended profile
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"status": "suspended"}]
        )
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token-123")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.get_current_user(credentials)
        
        assert exc_info.value.status_code == 403
        assert "Account suspended" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_no_user(self, auth_manager, mock_supabase_client):
        """Test current user retrieval with no user found"""
        # Mock no user found
        mock_supabase_client.auth.get_user.return_value = Mock(user=None)
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token-123")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_exception(self, auth_manager, mock_supabase_client):
        """Test current user retrieval with exception"""
        # Mock exception during user retrieval
        mock_supabase_client.auth.get_user.side_effect = Exception("Token expired")
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token-123")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Token expired" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_email_success(self, auth_manager, mock_supabase_client):
        """Test successful email verification"""
        # Mock successful verification
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        
        mock_supabase_client.auth.verify_otp.return_value = Mock(user=mock_user)
        
        # Mock profile update
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        result = await auth_manager.verify_email("valid-token")
        
        assert result["success"] is True
        assert "successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, auth_manager, mock_supabase_client):
        """Test email verification with invalid token"""
        # Mock invalid token
        mock_supabase_client.auth.verify_otp.return_value = Mock(user=None)
        
        result = await auth_manager.verify_email("invalid-token")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_reset_password_success(self, auth_manager, mock_supabase_client):
        """Test successful password reset"""
        # Mock successful password reset
        mock_supabase_client.auth.reset_password_email.return_value = Mock()
        
        result = await auth_manager.reset_password("test@example.com")
        
        assert result["success"] is True
        assert "sent" in result["message"]

    @pytest.mark.asyncio
    async def test_reset_password_exception(self, auth_manager, mock_supabase_client):
        """Test password reset with exception"""
        # Mock exception during password reset
        mock_supabase_client.auth.reset_password_email.side_effect = Exception("Reset failed")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.reset_password("test@example.com")
        
        assert exc_info.value.status_code == 400
        assert "Password reset failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_password_success(self, auth_manager, mock_supabase_client):
        """Test successful password update"""
        # Mock successful password update
        mock_user = Mock()
        mock_user.email = "test@example.com"
        
        mock_supabase_client.auth.set_session.return_value = None
        mock_supabase_client.auth.update_user.return_value = Mock(user=mock_user)
        
        result = await auth_manager.update_password("valid-token", "NewPassword123!")
        
        assert result["success"] is True
        assert "successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_update_password_failure(self, auth_manager, mock_supabase_client):
        """Test password update failure"""
        # Mock failed password update
        mock_supabase_client.auth.set_session.return_value = None
        mock_supabase_client.auth.update_user.return_value = Mock(user=None)
        
        result = await auth_manager.update_password("valid-token", "NewPassword123!")
        
        assert result["success"] is False
        assert "error" in result