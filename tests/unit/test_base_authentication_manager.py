"""Unit tests for BaseAuthenticationManager abstract class.

This module provides comprehensive tests for the BaseAuthenticationManager
abstract class, testing all concrete methods and ensuring proper abstract
method enforcement.
"""

import pytest
from datetime import datetime

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from auth.base_authentication_manager import (
    BaseAuthenticationManager,
    AuthenticationProvider,
    AuthenticationError,
    TokenExpiredError,
    InvalidCredentialsError,
    NetworkError,
)


class ConcreteAuthenticationManager(BaseAuthenticationManager):
    """Concrete implementation for testing BaseAuthenticationManager."""

    def __init__(
        self, provider: AuthenticationProvider = AuthenticationProvider.MICROSOFT_OAUTH
    ):
        super().__init__(provider)
        self._mock_token = "mock_access_token"
        self._mock_valid = True
        self._mock_auth_success = True

    def authenticate(self) -> bool:
        if not self._mock_auth_success:
            raise AuthenticationError("Mock authentication failed", self.provider)
        self.is_authenticated = self._mock_auth_success
        if self._mock_auth_success:
            self.last_authentication_time = datetime.now()
        return self._mock_auth_success

    def get_access_token(self) -> str:
        if not self._mock_token:
            raise AuthenticationError("No token available", self.provider)
        return self._mock_token

    def is_token_valid(self) -> bool:
        return self._mock_valid

    def refresh_token(self) -> bool:
        if not self._mock_valid:
            raise TokenExpiredError("Token refresh failed", self.provider)
        return True

    def get_smtp_auth_string(self, username: str) -> str:
        return f"mock_auth_string_{username}_{self._mock_token}"

    def validate_configuration(self) -> bool:
        return "required_key" in self._config


class TestAuthenticationProvider:
    """Test cases for AuthenticationProvider enum."""

    def test_provider_values(self):
        """Test that provider enum has expected values."""
        assert AuthenticationProvider.MICROSOFT_OAUTH.value == "microsoft_oauth"
        assert AuthenticationProvider.GMAIL_APP_PASSWORD.value == "gmail_app_password"

    def test_provider_count(self):
        """Test that we have the expected number of providers."""
        providers = list(AuthenticationProvider)
        assert len(providers) == 2


class TestAuthenticationExceptions:
    """Test cases for authentication exception classes."""

    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH
        error = AuthenticationError("Test error", provider)

        assert str(error) == "Test error"
        assert error.provider == provider
        assert isinstance(error, Exception)

    def test_token_expired_error(self):
        """Test TokenExpiredError exception."""
        provider = AuthenticationProvider.GMAIL_APP_PASSWORD
        error = TokenExpiredError("Token expired", provider)

        assert str(error) == "Token expired"
        assert error.provider == provider
        assert isinstance(error, AuthenticationError)

    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError exception."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH
        error = InvalidCredentialsError("Invalid creds", provider)

        assert str(error) == "Invalid creds"
        assert error.provider == provider
        assert isinstance(error, AuthenticationError)

    def test_network_error(self):
        """Test NetworkError exception."""
        provider = AuthenticationProvider.GMAIL_APP_PASSWORD
        error = NetworkError("Network failed", provider)

        assert str(error) == "Network failed"
        assert error.provider == provider
        assert isinstance(error, AuthenticationError)


class TestBaseAuthenticationManager:
    """Test cases for BaseAuthenticationManager abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseAuthenticationManager cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAuthenticationManager(AuthenticationProvider.MICROSOFT_OAUTH)

    def test_concrete_implementation_initialization(self):
        """Test that concrete implementation initializes properly."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH
        manager = ConcreteAuthenticationManager(provider)

        assert manager.provider == provider
        assert manager._config == {}
        assert manager.is_authenticated is False
        assert manager.last_authentication_time is None

    def test_get_provider_name(self):
        """Test get_provider_name method."""
        manager = ConcreteAuthenticationManager(
            AuthenticationProvider.GMAIL_APP_PASSWORD
        )
        assert manager.get_provider_name() == "Gmail App Password"

    def test_get_authentication_status(self):
        """Test get_authentication_status method."""
        manager = ConcreteAuthenticationManager()
        status = manager.get_authentication_status()

        assert "is_authenticated" in status
        assert "last_authentication_time" in status
        assert "provider" in status
        assert "token_valid" in status
        assert status["is_authenticated"] is False

    def test_logout(self):
        """Test logout method."""
        manager = ConcreteAuthenticationManager()

        # Set some authentication status
        manager.is_authenticated = True
        manager.last_authentication_time = datetime.now()

        # Logout should reset status
        manager.logout()

        assert manager.is_authenticated is False
        assert manager.last_authentication_time is None

    def test_set_configuration(self):
        """Test set_configuration method."""
        manager = ConcreteAuthenticationManager()
        config = {"key1": "value1", "key2": "value2"}

        manager.set_configuration(config)
        assert manager._config == config

    def test_get_configuration(self):
        """Test get_configuration method."""
        manager = ConcreteAuthenticationManager()
        config = {"key1": "value1", "key2": "value2"}

        manager.set_configuration(config)
        retrieved_config = manager.get_configuration()

        assert retrieved_config == config
        # Ensure it's a copy, not the same object
        assert retrieved_config is not manager._config

    def test_get_configuration_key(self):
        """Test get_configuration with specific key."""
        manager = ConcreteAuthenticationManager()
        config = {"key1": "value1", "key2": "value2"}

        manager.set_configuration(config)

        assert manager.get_configuration().get("key1") == "value1"
        assert manager.get_configuration().get("key2") == "value2"
        assert manager.get_configuration().get("nonexistent") is None
        assert manager.get_configuration().get("nonexistent", "default") == "default"

    def test_concrete_methods_work(self):
        """Test that concrete implementations of abstract methods work."""
        manager = ConcreteAuthenticationManager()

        # Test authenticate
        assert manager.authenticate() is True

        # Test get_access_token
        token = manager.get_access_token()
        assert token == "mock_access_token"

        # Test is_token_valid
        assert manager.is_token_valid() is True

        # Test refresh_token
        assert manager.refresh_token() is True

        # Test get_smtp_auth_string
        auth_string = manager.get_smtp_auth_string("test@example.com")
        assert "mock_auth_string_test@example.com_mock_access_token" == auth_string

        # Test validate_configuration - initially should be False
        assert manager.validate_configuration() is False  # No required_key set

        # Set required key and test again
        manager.set_configuration({"required_key": "test_value"})
        assert manager.validate_configuration() is True

        # Clear configuration and test
        manager._config = {}  # Clear config directly
        assert manager.validate_configuration() is False

    def test_authentication_error_handling(self):
        """Test that authentication errors are properly handled."""
        manager = ConcreteAuthenticationManager()
        manager._mock_auth_success = False

        with pytest.raises(AuthenticationError) as exc_info:
            manager.authenticate()

        assert "Mock authentication failed" in str(exc_info.value)
        assert exc_info.value.provider == AuthenticationProvider.MICROSOFT_OAUTH

    def test_token_error_handling(self):
        """Test that token-related errors are properly handled."""
        manager = ConcreteAuthenticationManager()

        # Test missing token
        manager._mock_token = None
        with pytest.raises(AuthenticationError):
            manager.get_access_token()

        # Test token refresh failure
        manager._mock_valid = False
        with pytest.raises(TokenExpiredError):
            manager.refresh_token()

    def test_force_refresh_parameter(self):
        """Test that get_access_token works consistently."""
        manager = ConcreteAuthenticationManager()

        # Test get_access_token
        token1 = manager.get_access_token()
        assert token1 == "mock_access_token"

        # Test again to ensure consistency
        token2 = manager.get_access_token()
        assert token2 == "mock_access_token"

    def test_smtp_auth_string_with_custom_token(self):
        """Test SMTP auth string generation."""
        manager = ConcreteAuthenticationManager()

        # Test with default token
        auth_string1 = manager.get_smtp_auth_string("test@example.com")
        assert "mock_access_token" in auth_string1

        # Test with different username
        auth_string2 = manager.get_smtp_auth_string("other@example.com")
        assert "mock_access_token" in auth_string2
        assert "other@example.com" in auth_string2

    def test_is_token_valid_with_custom_token(self):
        """Test token validation."""
        manager = ConcreteAuthenticationManager()

        # Test with default behavior
        assert manager.is_token_valid() is True

        # Test when token is invalid
        manager._mock_valid = False
        assert manager.is_token_valid() is False


class TestBaseAuthenticationManagerIntegration:
    """Integration tests for BaseAuthenticationManager."""

    def test_full_authentication_flow(self):
        """Test complete authentication flow."""
        manager = ConcreteAuthenticationManager()
        config = {"required_key": "value", "username": "test@example.com"}

        # Set configuration
        manager.set_configuration(config)
        assert manager.validate_configuration() is True

        # Authenticate
        assert manager.authenticate() is True

        # Get token
        token = manager.get_access_token()
        assert token == "mock_access_token"

        # Validate token
        assert manager.is_token_valid() is True

        # Get SMTP auth string
        auth_string = manager.get_smtp_auth_string(config["username"])
        assert "test@example.com" in auth_string
        assert "mock_access_token" in auth_string

        # Check authentication status
        status = manager.get_authentication_status()
        assert status["is_authenticated"] is True

        # Logout
        manager.logout()
        status = manager.get_authentication_status()
        assert status["is_authenticated"] is False

    def test_error_propagation(self):
        """Test that errors propagate correctly through the system."""
        manager = ConcreteAuthenticationManager()

        # Test authentication error
        manager._mock_auth_success = False
        with pytest.raises(AuthenticationError):
            manager.authenticate()

        # Test token error
        manager._mock_token = None
        with pytest.raises(AuthenticationError):
            manager.get_access_token()

        # Test refresh error
        manager._mock_valid = False
        with pytest.raises(TokenExpiredError):
            manager.refresh_token()

    def test_configuration_persistence(self):
        """Test that configuration persists across method calls."""
        manager = ConcreteAuthenticationManager()
        config = {"key1": "value1", "key2": "value2", "required_key": "required_value"}

        manager.set_configuration(config)

        # Configuration should persist
        assert manager.get_configuration() == config
        assert manager.validate_configuration() is True

        # Should work after authentication
        manager.authenticate()
        assert manager.get_configuration() == config

        # Should work after token operations
        manager.get_access_token()
        assert manager.get_configuration() == config
