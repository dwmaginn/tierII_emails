"""Unit tests for AuthenticationFactory class.

This module provides comprehensive tests for the AuthenticationFactory
class, testing provider registration, auto-detection, and manager creation.
"""

import pytest
from unittest.mock import patch
from datetime import datetime

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from auth.authentication_factory import AuthenticationFactory
from auth.base_authentication_manager import (
    BaseAuthenticationManager,
    AuthenticationProvider,
    AuthenticationError,
)


class MockAuthenticationManager(BaseAuthenticationManager):
    """Mock authentication manager for testing."""

    def __init__(self, provider: AuthenticationProvider):
        super().__init__(provider)
        self._mock_valid_config = True
        self._mock_auth_success = True

    def authenticate(self) -> bool:
        if self._mock_auth_success:
            self.is_authenticated = True
            self.last_authentication_time = datetime.now()
        return self._mock_auth_success

    def get_access_token(self, force_refresh: bool = False) -> str:
        return "mock_token"

    def is_token_valid(self, token=None) -> bool:
        return True

    def refresh_token(self) -> str:
        return "refreshed_token"

    def get_smtp_auth_string(self, username: str, token=None) -> str:
        return f"mock_auth_{username}"

    def validate_configuration(self) -> bool:
        return self._mock_valid_config


class InvalidManager:
    """Invalid manager class that doesn't inherit from BaseAuthenticationManager."""

    pass


class TestAuthenticationFactory:
    """Test cases for AuthenticationFactory class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = AuthenticationFactory()

    def test_factory_initialization(self):
        """Test that factory initializes properly."""
        assert isinstance(self.factory._providers, dict)
        assert len(self.factory._providers) == 0
        assert self.factory._logger is not None

    def test_register_provider_success(self):
        """Test successful provider registration."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH

        self.factory.register_provider(provider, MockAuthenticationManager)

        assert provider in self.factory._providers
        assert self.factory._providers[provider] == MockAuthenticationManager

    def test_register_provider_invalid_class(self):
        """Test registration with invalid manager class."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH

        with pytest.raises(ValueError) as exc_info:
            self.factory.register_provider(provider, InvalidManager)

        assert "must inherit from BaseAuthenticationManager" in str(exc_info.value)

    def test_get_available_providers_empty(self):
        """Test getting available providers when none registered."""
        providers = self.factory.get_available_providers()
        assert providers == []

    def test_get_available_providers_with_registered(self):
        """Test getting available providers with registered providers."""
        provider1 = AuthenticationProvider.MICROSOFT_OAUTH
        provider2 = AuthenticationProvider.GMAIL_APP_PASSWORD

        self.factory.register_provider(provider1, MockAuthenticationManager)
        self.factory.register_provider(provider2, MockAuthenticationManager)

        providers = self.factory.get_available_providers()
        assert len(providers) == 2
        assert provider1 in providers
        assert provider2 in providers

    def test_create_manager_with_specific_provider(self):
        """Test creating manager with specific provider."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH
        config = {"tenant_id": "test", "client_id": "test", "client_secret": "test"}

        self.factory.register_provider(provider, MockAuthenticationManager)

        manager = self.factory.create_manager(provider=provider, config=config)

        assert isinstance(manager, MockAuthenticationManager)
        assert manager.provider == provider
        assert manager.get_configuration() == config

    def test_create_manager_unregistered_provider(self):
        """Test creating manager with unregistered provider."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH

        with pytest.raises(ValueError) as exc_info:
            self.factory.create_manager(provider=provider)

        assert "is not registered" in str(exc_info.value)

    def test_create_manager_invalid_configuration(self):
        """Test creating manager with invalid configuration."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH
        config = {"invalid": "config"}

        self.factory.register_provider(provider, MockAuthenticationManager)

        # Mock the manager to return invalid configuration
        with patch.object(
            MockAuthenticationManager, "validate_configuration", return_value=False
        ):
            with pytest.raises(AuthenticationError) as exc_info:
                self.factory.create_manager(provider=provider, config=config)

            assert "Invalid configuration" in str(exc_info.value)

    def test_create_manager_auto_detect_microsoft(self):
        """Test auto-detection of Microsoft OAuth provider."""
        config = {
            "tenant_id": "test-tenant",
            "client_id": "test-client",
            "client_secret": "test-secret",
        }

        self.factory.register_provider(
            AuthenticationProvider.MICROSOFT_OAUTH, MockAuthenticationManager
        )

        manager = self.factory.create_manager(config=config, auto_detect=True)

        assert isinstance(manager, MockAuthenticationManager)
        assert manager.provider == AuthenticationProvider.MICROSOFT_OAUTH

    def test_create_manager_auto_detect_gmail(self):
        """Test auto-detection of Gmail App Password provider."""
        config = {
            "gmail_app_password": "test-password",
            "gmail_sender_email": "test@gmail.com",
        }

        self.factory.register_provider(
            AuthenticationProvider.GMAIL_APP_PASSWORD, MockAuthenticationManager
        )

        manager = self.factory.create_manager(config=config, auto_detect=True)

        assert isinstance(manager, MockAuthenticationManager)
        assert manager.provider == AuthenticationProvider.GMAIL_APP_PASSWORD

    def test_create_manager_auto_detect_smtp_server_outlook(self):
        """Test auto-detection based on Outlook SMTP server."""
        config = {"smtp_server": "smtp.office365.com"}

        self.factory.register_provider(
            AuthenticationProvider.MICROSOFT_OAUTH, MockAuthenticationManager
        )

        manager = self.factory.create_manager(config=config, auto_detect=True)

        assert manager.provider == AuthenticationProvider.MICROSOFT_OAUTH

    def test_create_manager_auto_detect_smtp_server_gmail(self):
        """Test auto-detection based on Gmail SMTP server."""
        config = {"smtp_server": "smtp.gmail.com"}

        self.factory.register_provider(
            AuthenticationProvider.GMAIL_APP_PASSWORD, MockAuthenticationManager
        )

        manager = self.factory.create_manager(config=config, auto_detect=True)

        assert manager.provider == AuthenticationProvider.GMAIL_APP_PASSWORD

    def test_create_manager_auto_detect_fails(self):
        """Test auto-detection failure when no suitable provider found."""
        config = {"unknown": "config"}

        with pytest.raises(AuthenticationError) as exc_info:
            self.factory.create_manager(config=config, auto_detect=True)

        assert "No suitable authentication provider found" in str(exc_info.value)

    def test_create_manager_no_auto_detect_no_provider(self):
        """Test creation failure when auto-detect disabled and no provider specified."""
        config = {"test": "config"}

        with pytest.raises(AuthenticationError):
            self.factory.create_manager(config=config, auto_detect=False)

    def test_create_with_fallback_success_primary(self):
        """Test fallback creation with successful primary provider."""
        primary = AuthenticationProvider.MICROSOFT_OAUTH
        fallback = [AuthenticationProvider.GMAIL_APP_PASSWORD]
        config = {"tenant_id": "test", "client_id": "test", "client_secret": "test"}

        self.factory.register_provider(primary, MockAuthenticationManager)
        self.factory.register_provider(
            AuthenticationProvider.GMAIL_APP_PASSWORD, MockAuthenticationManager
        )

        manager = self.factory.create_with_fallback(primary, fallback, config)

        assert manager.provider == primary

    def test_create_with_fallback_success_fallback(self):
        """Test fallback creation with failed primary but successful fallback."""
        primary = AuthenticationProvider.MICROSOFT_OAUTH
        fallback = [AuthenticationProvider.GMAIL_APP_PASSWORD]
        config = {"gmail_app_password": "test", "gmail_sender_email": "test@gmail.com"}

        # Register providers with different validation behavior
        class FailingManager(MockAuthenticationManager):
            def validate_configuration(self):
                return False

        self.factory.register_provider(primary, FailingManager)
        self.factory.register_provider(
            AuthenticationProvider.GMAIL_APP_PASSWORD, MockAuthenticationManager
        )

        manager = self.factory.create_with_fallback(primary, fallback, config)

        assert manager.provider == AuthenticationProvider.GMAIL_APP_PASSWORD

    def test_create_with_fallback_all_fail(self):
        """Test fallback creation when all providers fail."""
        primary = AuthenticationProvider.MICROSOFT_OAUTH
        fallback = [AuthenticationProvider.GMAIL_APP_PASSWORD]
        config = {"invalid": "config"}

        class FailingManager(MockAuthenticationManager):
            def validate_configuration(self):
                return False

        self.factory.register_provider(primary, FailingManager)
        self.factory.register_provider(
            AuthenticationProvider.GMAIL_APP_PASSWORD, FailingManager
        )

        with pytest.raises(AuthenticationError) as exc_info:
            self.factory.create_with_fallback(primary, fallback, config)

        assert "All authentication providers failed" in str(exc_info.value)

    def test_validate_provider_config_success(self):
        """Test successful provider configuration validation."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH
        config = {"valid": "config"}

        self.factory.register_provider(provider, MockAuthenticationManager)

        result = self.factory.validate_provider_config(provider, config)
        assert result is True

    def test_validate_provider_config_unregistered(self):
        """Test validation with unregistered provider."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH
        config = {"test": "config"}

        result = self.factory.validate_provider_config(provider, config)
        assert result is False

    def test_validate_provider_config_invalid(self):
        """Test validation with invalid configuration."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH
        config = {"invalid": "config"}

        class FailingManager(MockAuthenticationManager):
            def validate_configuration(self):
                return False

        self.factory.register_provider(provider, FailingManager)

        result = self.factory.validate_provider_config(provider, config)
        assert result is False

    def test_validate_provider_config_exception(self):
        """Test validation when exception occurs."""
        provider = AuthenticationProvider.MICROSOFT_OAUTH
        config = {"test": "config"}

        class ExceptionManager(MockAuthenticationManager):
            def validate_configuration(self):
                raise Exception("Validation error")

        self.factory.register_provider(provider, ExceptionManager)

        result = self.factory.validate_provider_config(provider, config)
        assert result is False

    def test_detect_provider_microsoft_keys(self):
        """Test provider detection with Microsoft OAuth keys."""
        config = {
            "tenant_id": "test-tenant",
            "client_id": "test-client",
            "client_secret": "test-secret",
        }

        detected = self.factory._detect_provider(config)
        assert detected == AuthenticationProvider.MICROSOFT_OAUTH

    def test_detect_provider_gmail_keys(self):
        """Test provider detection with Gmail App Password keys."""
        config = {
            "gmail_app_password": "test-password",
            "gmail_sender_email": "test@gmail.com",
        }

        detected = self.factory._detect_provider(config)
        assert detected == AuthenticationProvider.GMAIL_APP_PASSWORD

    def test_detect_provider_outlook_smtp(self):
        """Test provider detection with Outlook SMTP server."""
        config = {"smtp_server": "outlook.office365.com"}

        detected = self.factory._detect_provider(config)
        assert detected == AuthenticationProvider.MICROSOFT_OAUTH

    def test_detect_provider_gmail_smtp(self):
        """Test provider detection with Gmail SMTP server."""
        config = {"smtp_server": "smtp.gmail.com"}

        detected = self.factory._detect_provider(config)
        assert detected == AuthenticationProvider.GMAIL_APP_PASSWORD

    def test_detect_provider_no_match(self):
        """Test provider detection with no matching configuration."""
        config = {"unknown": "config"}

        detected = self.factory._detect_provider(config)
        assert detected is None

    def test_detect_provider_case_insensitive_smtp(self):
        """Test provider detection is case insensitive for SMTP servers."""
        config = {"smtp_server": "SMTP.GMAIL.COM"}

        detected = self.factory._detect_provider(config)
        assert detected == AuthenticationProvider.GMAIL_APP_PASSWORD


class TestAuthenticationFactoryIntegration:
    """Integration tests for AuthenticationFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = AuthenticationFactory()
        self.factory.register_provider(
            AuthenticationProvider.MICROSOFT_OAUTH, MockAuthenticationManager
        )
        self.factory.register_provider(
            AuthenticationProvider.GMAIL_APP_PASSWORD, MockAuthenticationManager
        )

    def test_full_workflow_microsoft(self):
        """Test complete workflow with Microsoft OAuth."""
        config = {
            "tenant_id": "test-tenant",
            "client_id": "test-client",
            "client_secret": "test-secret",
        }

        # Auto-detect should work
        manager = self.factory.create_manager(config=config)
        assert manager.provider == AuthenticationProvider.MICROSOFT_OAUTH

        # Should be able to authenticate
        assert manager.authenticate() is True

        # Should be able to get token
        token = manager.get_access_token()
        assert token == "mock_token"

    def test_full_workflow_gmail(self):
        """Test complete workflow with Gmail App Password."""
        config = {
            "gmail_app_password": "test-password",
            "gmail_sender_email": "test@gmail.com",
        }

        # Auto-detect should work
        manager = self.factory.create_manager(config=config)
        assert manager.provider == AuthenticationProvider.GMAIL_APP_PASSWORD

        # Should be able to authenticate
        assert manager.authenticate() is True

        # Should be able to get token
        token = manager.get_access_token()
        assert token == "mock_token"

    def test_fallback_workflow(self):
        """Test fallback workflow when primary provider fails."""
        config = {"gmail_app_password": "test", "gmail_sender_email": "test@gmail.com"}

        # Create manager that fails validation for Microsoft
        class FailingMicrosoftManager(MockAuthenticationManager):
            def validate_configuration(self):
                return self.provider != AuthenticationProvider.MICROSOFT_OAUTH

        # Replace Microsoft manager with failing one
        self.factory._providers[
            AuthenticationProvider.MICROSOFT_OAUTH
        ] = FailingMicrosoftManager

        # Should fallback to Gmail
        manager = self.factory.create_with_fallback(
            AuthenticationProvider.MICROSOFT_OAUTH,
            [AuthenticationProvider.GMAIL_APP_PASSWORD],
            config,
        )

        assert manager.provider == AuthenticationProvider.GMAIL_APP_PASSWORD
