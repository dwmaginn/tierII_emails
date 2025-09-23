"""Unit tests for MicrosoftOAuthManager class.

This module provides comprehensive tests for the MicrosoftOAuthManager
class, testing OAuth token management, SMTP authentication, and integration
with the existing OAuthTokenManager.
"""

import pytest
from unittest.mock import Mock, patch
import uuid

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from auth.microsoft_oauth_manager import MicrosoftOAuthManager
from auth.base_authentication_manager import (
    AuthenticationProvider,
    AuthenticationError,
    TokenExpiredError,
    InvalidCredentialsError,
)


class TestMicrosoftOAuthManager:
    """Test cases for MicrosoftOAuthManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MicrosoftOAuthManager()
        self.valid_config = {
            "tenant_id": "12345678-1234-1234-1234-123456789abc",
            "client_id": "87654321-4321-4321-4321-cba987654321",
            "client_secret": "test-client-secret",
            "sender_email": "test@outlook.com",
        }

    def test_initialization(self):
        """Test that manager initializes properly."""
        assert self.manager.provider == AuthenticationProvider.MICROSOFT_OAUTH
        assert self.manager._oauth_manager is None
        assert self.manager._logger is not None

    def test_set_configuration_valid(self):
        """Test setting valid configuration."""
        self.manager.set_configuration(self.valid_config)

        config = self.manager.get_configuration()
        assert config["tenant_id"] == "12345678-1234-1234-1234-123456789abc"
        assert config["client_id"] == "87654321-4321-4321-4321-cba987654321"
        assert config["client_secret"] == "test-client-secret"
        assert config["sender_email"] == "test@outlook.com"

    def test_validate_configuration_valid(self):
        """Test validation of valid configuration."""
        self.manager.set_configuration(self.valid_config)
        assert self.manager.validate_configuration() is True

    def test_validate_configuration_missing_tenant_id(self):
        """Test validation with missing tenant_id."""
        config = self.valid_config.copy()
        del config["tenant_id"]
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_configuration_missing_client_id(self):
        """Test validation with missing client_id."""
        config = self.valid_config.copy()
        del config["client_id"]
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_configuration_missing_client_secret(self):
        """Test validation with missing client_secret."""
        config = self.valid_config.copy()
        del config["client_secret"]
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_configuration_invalid_tenant_id_format(self):
        """Test validation with invalid tenant_id format."""
        config = self.valid_config.copy()
        config["tenant_id"] = "invalid-tenant"
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_configuration_invalid_email_format(self):
        """Test validation with invalid email format."""
        config = self.valid_config.copy()
        config["sender_email"] = "invalid-email"
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_configuration_non_microsoft_domain(self):
        """Test validation with non-Microsoft domain."""
        config = self.valid_config.copy()
        config["sender_email"] = "test@gmail.com"
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_uuid_valid(self):
        """Test UUID validation with valid UUID."""
        valid_uuid = str(uuid.uuid4())
        assert self.manager._is_valid_uuid(valid_uuid) is True

    def test_validate_uuid_invalid(self):
        """Test UUID validation with invalid UUID."""
        assert self.manager._is_valid_uuid("invalid-uuid") is False
        assert self.manager._is_valid_uuid("") is False
        assert self.manager._is_valid_uuid(None) is False

    def test_validate_microsoft_domain_valid(self):
        """Test Microsoft domain validation with valid domains."""
        valid_emails = [
            "test@outlook.com",
            "user@hotmail.com",
            "admin@live.com",
            "employee@company.onmicrosoft.com",
            "user@office365.com",
        ]

        for email in valid_emails:
            assert self.manager._is_microsoft_domain(email) is True

    def test_validate_microsoft_domain_invalid(self):
        """Test Microsoft domain validation with invalid domains."""
        invalid_emails = [
            "test@gmail.com",
            "user@yahoo.com",
            "admin@company.com",
            "invalid-email",
            "",
        ]

        for email in invalid_emails:
            assert self.manager._is_microsoft_domain(email) is False

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_authenticate_success(self, mock_oauth_class):
        """Test successful authentication."""
        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager
        mock_oauth_manager.get_access_token.return_value = "test-token"

        self.manager.set_configuration(self.valid_config)

        credentials = {
            "tenant_id": "12345678-1234-1234-1234-123456789abc",
            "client_id": "87654321-4321-4321-4321-cba987654321",
            "client_secret": "test-client-secret",
        }

        result = self.manager.authenticate(credentials)

        assert result is True
        assert self.manager._oauth_manager is not None
        mock_oauth_class.assert_called_once_with(
            tenant_id="12345678-1234-1234-1234-123456789abc",
            client_id="87654321-4321-4321-4321-cba987654321",
            client_secret="test-client-secret",
        )

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_authenticate_token_failure(self, mock_oauth_class):
        """Test authentication failure due to token retrieval error."""
        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager
        mock_oauth_manager.get_access_token.side_effect = Exception("Token error")

        self.manager.set_configuration(self.valid_config)

        credentials = {
            "tenant_id": "12345678-1234-1234-1234-123456789abc",
            "client_id": "87654321-4321-4321-4321-cba987654321",
            "client_secret": "test-client-secret",
        }

        with pytest.raises(AuthenticationError) as exc_info:
            self.manager.authenticate(credentials)

        assert "Authentication failed" in str(exc_info.value)

    def test_authenticate_missing_credentials(self):
        """Test authentication with missing credentials."""
        # Use fresh manager without pre-setting valid config
        fresh_manager = MicrosoftOAuthManager()

        credentials = {
            "tenant_id": "12345678-1234-1234-1234-123456789abc"
        }  # Missing client_id and client_secret

        with pytest.raises(InvalidCredentialsError):
            fresh_manager.authenticate(credentials)

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_get_access_token_success(self, mock_oauth_class):
        """Test successful token retrieval."""
        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager
        mock_oauth_manager.get_access_token.return_value = "test-access-token"

        self.manager.set_configuration(self.valid_config)
        self.manager._oauth_manager = mock_oauth_manager

        token = self.manager.get_access_token()

        assert token == "test-access-token"
        mock_oauth_manager.get_access_token.assert_called_once()

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_get_access_token_force_refresh(self, mock_oauth_class):
        """Test token retrieval with force refresh."""
        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager
        mock_oauth_manager.get_access_token.return_value = "refreshed-token"

        self.manager.set_configuration(self.valid_config)
        self.manager._oauth_manager = mock_oauth_manager

        token = self.manager.get_access_token(force_refresh=True)

        assert token == "refreshed-token"
        mock_oauth_manager.get_access_token.assert_called_once()

    def test_get_access_token_no_oauth_manager(self):
        """Test token retrieval without OAuth manager."""
        self.manager.set_configuration(self.valid_config)

        with pytest.raises(AuthenticationError) as exc_info:
            self.manager.get_access_token()

        assert "OAuthTokenManager not available" in str(exc_info.value)

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_get_access_token_with_caching(self, mock_oauth_class):
        """Test token retrieval with caching."""
        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager
        mock_oauth_manager.get_access_token.return_value = "cached-token"

        self.manager.set_configuration(self.valid_config)
        self.manager._oauth_manager = mock_oauth_manager

        # Set up caching by setting current token and expiry
        from datetime import datetime, timedelta

        self.manager._current_token = "cached-token"
        self.manager._token_expiry = datetime.now() + timedelta(minutes=30)

        # First call should get the cached token
        token1 = self.manager.get_access_token()
        # Second call should also get the cached token
        token2 = self.manager.get_access_token()

        assert token1 == "cached-token"
        assert token2 == "cached-token"
        # Should not call OAuth manager due to caching
        assert mock_oauth_manager.get_access_token.call_count == 0

    def test_is_token_valid_with_valid_token(self):
        """Test token validation with valid token."""
        # Mock a valid token (long enough string > 50 chars)
        long_token = "a" * 60  # 60 character token
        result = self.manager.is_token_valid(long_token)
        assert result is True

    def test_is_token_valid_with_invalid_token(self):
        """Test token validation with invalid tokens."""
        invalid_tokens = [None, "", "   "]

        for token in invalid_tokens:
            result = self.manager.is_token_valid(token)
            assert result is False

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_is_token_valid_from_cache(self, mock_oauth_class):
        """Test token validation using current token."""
        from datetime import datetime, timedelta

        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager

        self.manager.set_configuration(self.valid_config)
        self.manager._oauth_manager = mock_oauth_manager
        self.manager._current_token = "cached-token"
        self.manager._token_expiry = datetime.now() + timedelta(
            minutes=30
        )  # Valid for 30 more minutes

        result = self.manager.is_token_valid()
        assert result is True

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_refresh_token_success(self, mock_oauth_class):
        """Test successful token refresh."""
        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager
        mock_oauth_manager.get_access_token.return_value = "refreshed-token"

        self.manager.set_configuration(self.valid_config)
        self.manager._oauth_manager = mock_oauth_manager

        token = self.manager.refresh_token()

        assert token == "refreshed-token"
        # The refresh_token method calls get_access_token without parameters on the OAuthTokenManager
        mock_oauth_manager.get_access_token.assert_called_once()

    def test_refresh_token_no_oauth_manager(self):
        """Test token refresh without OAuth manager."""
        self.manager.set_configuration(self.valid_config)

        with pytest.raises(AuthenticationError) as exc_info:
            self.manager.refresh_token()

        assert "OAuthTokenManager not available" in str(exc_info.value)

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_refresh_token_failure(self, mock_oauth_class):
        """Test token refresh failure."""
        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager
        mock_oauth_manager.get_access_token.side_effect = Exception("Refresh failed")

        self.manager.set_configuration(self.valid_config)
        self.manager._oauth_manager = mock_oauth_manager

        with pytest.raises(TokenExpiredError) as exc_info:
            self.manager.refresh_token()

        assert "Failed to refresh token" in str(exc_info.value)

    def test_get_smtp_auth_string_with_token(self):
        """Test SMTP auth string generation with provided token."""
        username = "test@outlook.com"
        token = "test-access-token"

        auth_string = self.manager.get_smtp_auth_string(username, token)

        # Should return base64 encoded OAuth string
        import base64

        expected = base64.b64encode(
            f"user={username}\x01auth=Bearer {token}\x01\x01".encode()
        ).decode()
        assert auth_string == expected

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_get_smtp_auth_string_without_token(self, mock_oauth_class):
        """Test SMTP auth string generation without provided token."""
        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager
        mock_oauth_manager.get_access_token.return_value = "auto-token"

        self.manager.set_configuration(self.valid_config)
        self.manager._oauth_manager = mock_oauth_manager

        username = "test@outlook.com"
        auth_string = self.manager.get_smtp_auth_string(username)

        # Should retrieve token automatically and return auth string
        import base64

        expected = base64.b64encode(
            f"user={username}\x01auth=Bearer auto-token\x01\x01".encode()
        ).decode()
        assert auth_string == expected

    def test_get_smtp_auth_string_no_token_no_oauth(self):
        """Test SMTP auth string generation without token or OAuth manager."""
        self.manager.set_configuration(self.valid_config)

        username = "test@outlook.com"

        with pytest.raises(AuthenticationError) as exc_info:
            self.manager.get_smtp_auth_string(username)

        assert "OAuthTokenManager not available" in str(exc_info.value)

    def test_logout(self):
        """Test logout functionality."""
        # Set up some state
        self.manager.set_configuration(self.valid_config)
        self.manager._oauth_manager = Mock()
        self.manager._current_token = "test-token"

        self.manager.logout()

        # Should clear OAuth manager and current token
        assert self.manager._oauth_manager is None
        assert self.manager._current_token is None

    def test_get_authentication_status_authenticated(self):
        """Test authentication status when authenticated."""
        self.manager.set_configuration(self.valid_config)
        self.manager._oauth_manager = Mock()
        self.manager.is_authenticated = True

        status = self.manager.get_authentication_status()

        assert status["is_authenticated"] is True
        assert status["provider"] == "microsoft_oauth"
        assert "last_authentication_time" in status

    def test_get_authentication_status_not_authenticated(self):
        """Test authentication status when not authenticated."""
        status = self.manager.get_authentication_status()

        assert status["is_authenticated"] is False
        assert status["provider"] == "microsoft_oauth"
        assert status["last_authentication_time"] is None


class TestMicrosoftOAuthManagerIntegration:
    """Integration tests for MicrosoftOAuthManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MicrosoftOAuthManager()
        self.valid_config = {
            "tenant_id": str(uuid.uuid4()),
            "client_id": str(uuid.uuid4()),
            "client_secret": "test-secret-123",
            "sender_email": "test@outlook.com",
        }

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_full_authentication_workflow(self, mock_oauth_class):
        """Test complete authentication workflow."""
        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager
        mock_oauth_manager.get_access_token.return_value = (
            "workflow-token-" + "x" * 50
        )  # Make it longer than 50 chars

        # Set configuration
        self.manager.set_configuration(self.valid_config)
        assert self.manager.validate_configuration() is True

        # Authenticate
        credentials = {
            "tenant_id": self.valid_config["tenant_id"],
            "client_id": self.valid_config["client_id"],
            "client_secret": self.valid_config["client_secret"],
        }

        result = self.manager.authenticate(credentials)
        assert result is True

        # Get access token
        token = self.manager.get_access_token()
        expected_token = "workflow-token-" + "x" * 50
        assert token == expected_token

        # Validate token
        assert self.manager.is_token_valid(token) is True

        # Get SMTP auth string
        auth_string = self.manager.get_smtp_auth_string("test@outlook.com")
        assert auth_string is not None
        assert len(auth_string) > 0

        # Check authentication status
        status = self.manager.get_authentication_status()
        assert status["is_authenticated"] is True

        # Logout
        self.manager.logout()
        status = self.manager.get_authentication_status()
        assert status["is_authenticated"] is False

    @patch("auth.microsoft_oauth_manager.OAuthTokenManager")
    def test_token_refresh_workflow(self, mock_oauth_class):
        """Test token refresh workflow."""
        mock_oauth_manager = Mock()
        mock_oauth_class.return_value = mock_oauth_manager

        # First call returns original token, second call returns refreshed token
        mock_oauth_manager.get_access_token.side_effect = [
            "original-token",
            "refreshed-token",
        ]

        self.manager.set_configuration(self.valid_config)
        self.manager._oauth_manager = mock_oauth_manager

        # Get initial token
        token1 = self.manager.get_access_token()
        assert token1 == "original-token"

        # Refresh token
        token2 = self.manager.refresh_token()
        assert token2 == "refreshed-token"

        # Verify OAuth manager was called twice
        assert mock_oauth_manager.get_access_token.call_count == 2

    def test_configuration_validation_edge_cases(self):
        """Test configuration validation with various edge cases."""
        # Test with minimal valid configuration
        minimal_config = {
            "tenant_id": str(uuid.uuid4()),
            "client_id": str(uuid.uuid4()),
            "client_secret": "secret",
        }

        self.manager.set_configuration(minimal_config)
        assert self.manager.validate_configuration() is True

        # Test with extra fields (should still be valid)
        extended_config = minimal_config.copy()
        extended_config.update(
            {"sender_email": "test@outlook.com", "extra_field": "extra_value"}
        )

        self.manager.set_configuration(extended_config)
        assert self.manager.validate_configuration() is True

        # Test with empty strings (should be invalid)
        invalid_config = {
            "tenant_id": "",
            "client_id": str(uuid.uuid4()),
            "client_secret": "secret",
        }

        self.manager.set_configuration(invalid_config)
        assert self.manager.validate_configuration() is False
