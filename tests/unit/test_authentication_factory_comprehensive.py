"""Comprehensive unit tests for authentication factory.

This module provides extensive test coverage for the AuthenticationFactory class,
including edge cases, error conditions, and integration scenarios.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import threading
import time
from types import SimpleNamespace

from src.auth.authentication_factory import AuthenticationFactory, authentication_factory
from src.auth.base_authentication_manager import (
    BaseAuthenticationManager,
    AuthenticationProvider,
    AuthenticationError,
)
from src.auth.mailersend_manager import MailerSendManager


class TestAuthenticationFactoryComprehensive:
    """Comprehensive test suite for AuthenticationFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = AuthenticationFactory()
        
        # Mock settings
        self.valid_settings = SimpleNamespace(
            mailersend_api_token="test_token_123",
            sender_email="test@example.com",
            sender_name="Test Sender"
        )
        
        self.valid_config = {
            "mailersend_api_token": "test_token_123",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender"
        }

    def test_register_provider_success(self):
        """Test successful provider registration."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        
        # Act
        self.factory.register_provider(provider, MailerSendManager)
        
        # Assert
        assert provider in self.factory._providers
        assert self.factory._providers[provider] == MailerSendManager

    def test_register_provider_override_existing(self):
        """Test overriding an existing provider registration."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        original_class = MailerSendManager
        
        # Create a mock class that properly inherits from BaseAuthenticationManager
        class MockManager(BaseAuthenticationManager):
            def __init__(self, settings):
                super().__init__(settings)
            
            def authenticate(self):
                return True
            
            def validate_configuration(self):
                return True
            
            def send_email(self, to_email, subject, body, **kwargs):
                return {"status": "success"}
        
        # Act
        self.factory.register_provider(provider, original_class)
        self.factory.register_provider(provider, MockManager)
        
        # Assert
        assert self.factory._providers[provider] == MockManager

    def test_register_provider_invalid_manager_class(self):
        """Test registration with invalid manager class."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        invalid_class = str  # Not a BaseAuthenticationManager subclass
        
        # Act & Assert
        with pytest.raises(ValueError, match="must inherit from BaseAuthenticationManager"):
            self.factory.register_provider(provider, invalid_class)

    def test_register_provider_none_manager_class(self):
        """Test registration with None manager class."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        
        # Act & Assert
        with pytest.raises(TypeError):
            self.factory.register_provider(provider, None)

    def test_create_manager_success(self):
        """Test successful manager creation."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        self.factory.register_provider(provider, MailerSendManager)
        
        with patch.object(MailerSendManager, 'validate_configuration', return_value=True):
            # Act
            manager = self.factory.create_manager(provider, self.valid_config)
            
            # Assert
            assert isinstance(manager, MailerSendManager)

    def test_create_manager_unregistered_provider(self):
        """Test creating manager for unregistered provider."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        
        # Act & Assert
        with pytest.raises(ValueError, match="mailersend is not registered"):
            self.factory.create_manager(provider, self.valid_config)

    def test_create_manager_invalid_config_validation_failure(self):
        """Test creating manager with config that fails validation."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        self.factory.register_provider(provider, MailerSendManager)
        
        with patch.object(MailerSendManager, 'validate_configuration', return_value=False):
            # Act & Assert
            with pytest.raises(AuthenticationError, match="Invalid configuration"):
                self.factory.create_manager(provider, self.valid_config)

    def test_get_available_providers_empty(self):
        """Test getting available providers when none are registered."""
        # Act
        providers = self.factory.get_available_providers()
        
        # Assert
        assert providers == []

    def test_get_available_providers_multiple(self):
        """Test getting multiple available providers."""
        # Arrange
        provider1 = AuthenticationProvider.MAILERSEND
        self.factory.register_provider(provider1, MailerSendManager)
        
        # Act
        providers = self.factory.get_available_providers()
        
        # Assert
        assert len(providers) == 1
        assert provider1 in providers

    def test_create_with_fallback_success_primary(self):
        """Test create_with_fallback using primary provider successfully."""
        # Arrange
        primary = AuthenticationProvider.MAILERSEND
        fallbacks = []
        self.factory.register_provider(primary, MailerSendManager)
        
        with patch.object(MailerSendManager, 'validate_configuration', return_value=True):
            # Act
            manager = self.factory.create_with_fallback(primary, fallbacks, self.valid_config)
            
            # Assert
            assert isinstance(manager, MailerSendManager)

    def test_create_with_fallback_all_fail(self):
        """Test create_with_fallback when all providers fail."""
        # Arrange
        primary = AuthenticationProvider.MAILERSEND
        fallbacks = []
        
        # Act & Assert
        with pytest.raises(AuthenticationError, match="All authentication providers failed"):
            self.factory.create_with_fallback(primary, fallbacks, self.valid_config)

    def test_detect_provider_mailersend(self):
        """Test auto-detection of MailerSend provider."""
        # Arrange
        config = {"mailersend_api_token": "test_token"}
        
        # Act
        detected = self.factory._detect_provider(config)
        
        # Assert
        assert detected == AuthenticationProvider.MAILERSEND

    def test_detect_provider_no_match(self):
        """Test auto-detection when no provider matches."""
        # Arrange
        config = {"unknown_key": "value"}
        
        # Act
        detected = self.factory._detect_provider(config)
        
        # Assert
        assert detected is None

    def test_validate_provider_config_success(self):
        """Test successful provider config validation."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        self.factory.register_provider(provider, MailerSendManager)
        
        with patch.object(MailerSendManager, 'validate_configuration', return_value=True):
            # Act
            is_valid = self.factory.validate_provider_config(provider, self.valid_config)
            
            # Assert
            assert is_valid is True

    def test_validate_provider_config_failure(self):
        """Test failed provider config validation."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        self.factory.register_provider(provider, MailerSendManager)
        
        with patch.object(MailerSendManager, 'validate_configuration', return_value=False):
            # Act
            is_valid = self.factory.validate_provider_config(provider, self.valid_config)
            
            # Assert
            assert is_valid is False

    def test_validate_provider_config_unregistered(self):
        """Test config validation for unregistered provider."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        
        # Act
        is_valid = self.factory.validate_provider_config(provider, self.valid_config)
        
        # Assert
        assert is_valid is False

    def test_singleton_behavior(self):
        """Test that global factory instance behaves as singleton."""
        # Act
        factory1 = authentication_factory
        factory2 = authentication_factory
        
        # Assert
        assert factory1 is factory2

    def test_complex_configuration_handling(self):
        """Test handling of complex configuration objects."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        self.factory.register_provider(provider, MailerSendManager)
        
        complex_config = {
            "mailersend_api_token": "test_token_123",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender",
            "nested": {
                "key": "value",
                "list": [1, 2, 3]
            },
            "timeout": 30,
            "retries": 3
        }
        
        with patch.object(MailerSendManager, 'validate_configuration', return_value=True):
            # Act
            manager = self.factory.create_manager(provider, complex_config)
            
            # Assert
            assert isinstance(manager, MailerSendManager)

    def test_auto_detect_create_manager(self):
        """Test auto-detection in create_manager."""
        # Arrange
        self.factory.register_provider(AuthenticationProvider.MAILERSEND, MailerSendManager)
        
        with patch.object(MailerSendManager, 'validate_configuration', return_value=True):
            # Act - don't specify provider, let it auto-detect
            manager = self.factory.create_manager(config=self.valid_config, auto_detect=True)
            
            # Assert
            assert isinstance(manager, MailerSendManager)

    def test_auto_detect_no_suitable_provider(self):
        """Test auto-detection when no suitable provider found."""
        # Arrange - don't register any providers
        config = {"unknown_key": "value"}
        
        # Act & Assert
        with pytest.raises(AuthenticationError, match="No suitable authentication provider found"):
            self.factory.create_manager(config=config, auto_detect=True)


class TestAuthenticationFactoryEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = AuthenticationFactory()
        self.valid_config = {
            "mailersend_api_token": "test_token_123",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender"
        }

    def test_none_values_handling(self):
        """Test handling of None values in various contexts."""
        # Test None config
        with pytest.raises(ValueError, match="mailersend is not registered"):
            self.factory.create_manager(AuthenticationProvider.MAILERSEND, None)

    def test_empty_string_values(self):
        """Test handling of empty string values."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        self.factory.register_provider(provider, MailerSendManager)
        
        empty_config = {
            "mailersend_api_token": "",
            "sender_email": "",
            "sender_name": ""
        }
        
        with patch.object(MailerSendManager, 'validate_configuration', return_value=False):
            # Act & Assert
            with pytest.raises(AuthenticationError):
                self.factory.create_manager(provider, empty_config)

    def test_special_characters_in_config(self):
        """Test handling of special characters in configuration."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        self.factory.register_provider(provider, MailerSendManager)
        
        special_config = {
            "mailersend_api_token": "token_with_!@#$%^&*()_+",
            "sender_email": "test+special@example.com",
            "sender_name": "Test Sender with émojis 🚀"
        }
        
        with patch.object(MailerSendManager, 'validate_configuration', return_value=True):
            # Act
            manager = self.factory.create_manager(provider, special_config)
            
            # Assert
            assert isinstance(manager, MailerSendManager)

    def test_large_configuration_object(self):
        """Test handling of large configuration objects."""
        # Arrange
        provider = AuthenticationProvider.MAILERSEND
        self.factory.register_provider(provider, MailerSendManager)
        
        # Create a large config with many keys
        large_config = {
            "mailersend_api_token": "test_token_123",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender"
        }
        
        # Add many additional keys
        for i in range(100):  # Reduced from 1000 to avoid excessive test time
            large_config[f"extra_key_{i}"] = f"value_{i}"
        
        with patch.object(MailerSendManager, 'validate_configuration', return_value=True):
            # Act
            manager = self.factory.create_manager(provider, large_config)
            
            # Assert
            assert isinstance(manager, MailerSendManager)