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

    def __init__(self, settings):
        super().__init__(AuthenticationProvider.MAILERSEND)
        self.settings = settings
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

    def test_factory_singleton_behavior(self):
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
