"""Unit tests for AuthenticationFactory class.

This module provides comprehensive tests for the AuthenticationFactory
class, testing provider registration and MailerSend manager creation.
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


class MockMailerSendManager(BaseAuthenticationManager):
    """Mock MailerSend authentication manager for testing."""

    def __init__(self, provider):
        super().__init__(provider)
        self._mock_valid_config = True
        self._mock_auth_success = True

    def authenticate(self) -> bool:
        if self._mock_auth_success:
            self.is_authenticated = True
            self.last_authentication_time = datetime.now()
        return self._mock_auth_success

    def get_access_token(self, force_refresh: bool = False) -> str:
        return "mock_mailersend_token"

    def is_token_valid(self, token=None) -> bool:
        return True

    def refresh_token(self) -> str:
        return "refreshed_mailersend_token"

    def send_email(self, recipient_email: str, subject: str, body: str, 
                   sender_email: str, sender_name: str) -> bool:
        """Mock email sending method."""
        return True

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
        assert self.factory._logger is not None

    def test_register_provider_success(self):
        """Test successful provider registration."""
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        assert AuthenticationProvider.MAILERSEND in self.factory._providers
        assert self.factory._providers[AuthenticationProvider.MAILERSEND] == MockMailerSendManager

    def test_register_provider_invalid_manager(self):
        """Test registration with invalid manager class."""
        with pytest.raises(ValueError, match="Manager class .* must inherit from BaseAuthenticationManager"):
            self.factory.register_provider(
                AuthenticationProvider.MAILERSEND, InvalidManager
            )

    def test_create_manager_mailersend_success(self):
        """Test successful MailerSend manager creation."""
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        
        config = {
            "mailersend_api_token": "test_token",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender"
        }
        
        manager = self.factory.create_manager(AuthenticationProvider.MAILERSEND, config)
        
        assert isinstance(manager, MockMailerSendManager)
        assert manager.provider == AuthenticationProvider.MAILERSEND

    def test_create_manager_unregistered_provider(self):
        """Test creation with unregistered provider."""
        config = {"mailersend_api_token": "test_token"}
        
        with pytest.raises(ValueError, match="Provider .* is not registered"):
            self.factory.create_manager(AuthenticationProvider.MAILERSEND, config)

    def test_create_manager_invalid_config(self):
        """Test creation with invalid configuration."""
        # Mock a manager that fails validation
        class InvalidConfigManager(MockMailerSendManager):
            def validate_configuration(self) -> bool:
                return False
        
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, InvalidConfigManager
        )
        
        config = {"invalid": "config"}
        
        with pytest.raises(AuthenticationError, match="Invalid configuration"):
            self.factory.create_manager(AuthenticationProvider.MAILERSEND, config)


class TestAuthenticationFactoryIntegration:
    """Integration tests for AuthenticationFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = AuthenticationFactory()
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )

    def test_end_to_end_mailersend_workflow(self):
        """Test complete MailerSend authentication workflow."""
        config = {
            "mailersend_api_token": "test_token",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender"
        }
        
        # Create manager
        manager = self.factory.create_manager(AuthenticationProvider.MAILERSEND, config)
        
        # Test authentication
        assert manager.authenticate() is True
        assert manager.is_authenticated is True
        
        # Test token operations
        token = manager.get_access_token()
        assert token == "mock_mailersend_token"
        assert manager.is_token_valid(token) is True
        
        # Test email sending
        success = manager.send_email(
            recipient_email="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            sender_email="sender@example.com",
            sender_name="Test Sender"
        )
        assert success is True

    def test_factory_caching_behavior(self):
        """Test that factory uses caching to prevent redundant manager creation."""
        from src.auth.authentication_cache import authentication_cache
        
        # Clear cache first
        authentication_cache.invalidate_cache()
        
        config = {
            "mailersend_api_token": "test_token",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender"
        }
        
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        
        # Create first manager
        manager1 = self.factory.create_manager(AuthenticationProvider.MAILERSEND, config)
        
        # Create second manager with same config - should return cached instance
        manager2 = self.factory.create_manager(AuthenticationProvider.MAILERSEND, config)
        
        # Should be the same instance due to caching
        assert manager1 is manager2
        
        # Clean up
        authentication_cache.invalidate_cache()

    def test_factory_cache_invalidation(self):
        """Test that cache invalidation forces new manager creation."""
        from src.auth.authentication_cache import authentication_cache
        
        # Clear cache first
        authentication_cache.invalidate_cache()
        
        config = {
            "mailersend_api_token": "test_token",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender"
        }
        
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        
        # Create first manager
        manager1 = self.factory.create_manager(AuthenticationProvider.MAILERSEND, config)
        print(f"Manager1 ID: {id(manager1)}")
        print(f"Manager1 authenticated: {manager1.is_authenticated}")
        
        # Keep a strong reference to prevent garbage collection
        managers_list = [manager1]
        
        # Check cache stats before invalidation
        stats_before = authentication_cache.get_cache_stats()
        print(f"Cache stats before invalidation: {stats_before}")
        
        # Verify manager is cached
        cached_manager = authentication_cache.get_manager(AuthenticationProvider.MAILERSEND, config)
        print(f"Cached manager ID: {id(cached_manager) if cached_manager else 'None'}")
        
        # Invalidate cache
        authentication_cache.invalidate_cache(AuthenticationProvider.MAILERSEND)
        
        # Check cache stats after invalidation
        stats_after = authentication_cache.get_cache_stats()
        print(f"Cache stats after invalidation: {stats_after}")
        
        # Verify cache is empty
        cached_manager_after = authentication_cache.get_manager(AuthenticationProvider.MAILERSEND, config)
        print(f"Cached manager after invalidation: {id(cached_manager_after) if cached_manager_after else 'None'}")
        
        # Create second manager - should be new instance
        manager2 = self.factory.create_manager(AuthenticationProvider.MAILERSEND, config)
        print(f"Manager2 ID: {id(manager2)}")
        print(f"Manager2 authenticated: {manager2.is_authenticated}")
        
        # Should be different instances
        assert manager1 is not manager2
        
        # Clean up
        authentication_cache.invalidate_cache()
        """Test that factory maintains provider registrations."""
        # Register provider
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        
        # Create multiple managers
        config = {"mailersend_api_token": "test_token"}
        manager1 = self.factory.create_manager(AuthenticationProvider.MAILERSEND, config)
        manager2 = self.factory.create_manager(AuthenticationProvider.MAILERSEND, config)
        
        # Both should be instances of the same class
        assert type(manager1) == type(manager2)
        assert isinstance(manager1, MockMailerSendManager)
        assert isinstance(manager2, MockMailerSendManager)

    def test_get_available_providers(self):
        """Test getting list of available providers."""
        # Create a fresh factory instance to avoid interference from setup_method
        fresh_factory = AuthenticationFactory()
        
        # Initially empty
        assert fresh_factory.get_available_providers() == []
        
        # After registration
        fresh_factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        providers = fresh_factory.get_available_providers()
        assert AuthenticationProvider.MAILERSEND in providers
        assert len(providers) == 1

    def test_auto_detect_provider_success(self):
        """Test successful auto-detection of provider."""
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        
        config = {
            "mailersend_api_token": "test_token",
            "sender_email": "test@example.com"
        }
        
        # Should auto-detect MailerSend
        manager = self.factory.create_manager(config=config, auto_detect=True)
        assert isinstance(manager, MockMailerSendManager)

    def test_auto_detect_provider_failure(self):
        """Test auto-detection failure when no suitable provider found."""
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        
        config = {"unknown_key": "value"}
        
        with pytest.raises(AuthenticationError, match="No suitable authentication provider found"):
            self.factory.create_manager(config=config, auto_detect=True)

    def test_create_with_fallback_success_primary(self):
        """Test fallback mechanism when primary provider succeeds."""
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        
        config = {"mailersend_api_token": "test_token"}
        
        manager = self.factory.create_with_fallback(
            primary_provider=AuthenticationProvider.MAILERSEND,
            fallback_providers=[],
            config=config
        )
        
        assert isinstance(manager, MockMailerSendManager)

    def test_create_with_fallback_all_fail(self):
        """Test fallback mechanism when all providers fail."""
        # Mock a manager that always fails validation
        class FailingManager(MockMailerSendManager):
            def validate_configuration(self) -> bool:
                return False
        
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, FailingManager
        )
        
        config = {"invalid": "config"}
        
        with pytest.raises(AuthenticationError, match="All authentication providers failed"):
            self.factory.create_with_fallback(
                primary_provider=AuthenticationProvider.MAILERSEND,
                fallback_providers=[],
                config=config
            )

    def test_detect_provider_mailersend(self):
        """Test detection of MailerSend provider."""
        config = {"mailersend_api_token": "test_token"}
        detected = self.factory._detect_provider(config)
        assert detected == AuthenticationProvider.MAILERSEND

    def test_detect_provider_none(self):
        """Test detection returns None for unknown config."""
        config = {"unknown_key": "value"}
        detected = self.factory._detect_provider(config)
        assert detected is None

    def test_validate_provider_config_success(self):
        """Test successful provider configuration validation."""
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        
        config = {"mailersend_api_token": "test_token"}
        
        is_valid = self.factory.validate_provider_config(
            AuthenticationProvider.MAILERSEND, config
        )
        assert is_valid is True

    def test_validate_provider_config_unregistered(self):
        """Test validation with unregistered provider."""
        # Create a fresh factory instance without any registered providers
        fresh_factory = AuthenticationFactory()
        
        config = {"mailersend_api_token": "test_token"}
        
        is_valid = fresh_factory.validate_provider_config(
            AuthenticationProvider.MAILERSEND, config
        )
        assert is_valid is False

    def test_validate_provider_config_invalid(self):
        """Test validation with invalid configuration."""
        # Mock a manager that fails validation
        class InvalidConfigManager(MockMailerSendManager):
            def validate_configuration(self) -> bool:
                return False
        
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, InvalidConfigManager
        )
        
        config = {"invalid": "config"}
        
        is_valid = self.factory.validate_provider_config(
            AuthenticationProvider.MAILERSEND, config
        )
        assert is_valid is False

    def test_validate_provider_config_exception(self):
        """Test validation when exception occurs during validation."""
        # Mock a manager that raises exception during instantiation
        class ExceptionManager(MockMailerSendManager):
            def __init__(self, settings):
                raise ValueError("Test exception")
        
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, ExceptionManager
        )
        
        config = {"mailersend_api_token": "test_token"}
        
        is_valid = self.factory.validate_provider_config(
            AuthenticationProvider.MAILERSEND, config
        )
        assert is_valid is False

    def test_factory_with_settings(self):
        """Test factory initialization with settings."""
        from types import SimpleNamespace
        settings = SimpleNamespace(test_setting="value")
        factory = AuthenticationFactory(settings)
        assert factory._settings == settings

    def test_create_manager_no_config(self):
        """Test creating manager without config parameter."""
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        
        manager = self.factory.create_manager(AuthenticationProvider.MAILERSEND)
        assert isinstance(manager, MockMailerSendManager)

    def test_create_manager_auto_detect_disabled(self):
        """Test creating manager with auto_detect disabled."""
        self.factory.register_provider(
            AuthenticationProvider.MAILERSEND, MockMailerSendManager
        )
        
        config = {"mailersend_api_token": "test_token"}
        
        with pytest.raises(AuthenticationError, match="No suitable authentication provider found"):
            self.factory.create_manager(config=config, auto_detect=False)
