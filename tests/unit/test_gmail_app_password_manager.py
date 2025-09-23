"""Unit tests for GmailAppPasswordManager class.

This module provides comprehensive tests for the GmailAppPasswordManager
class, testing app password authentication, SMTP connection validation,
and Gmail-specific functionality.
"""

import pytest
from unittest.mock import Mock, patch
import smtplib
import socket

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from auth.gmail_app_password_manager import GmailAppPasswordManager
from auth.base_authentication_manager import (
    AuthenticationProvider,
    AuthenticationError,
    InvalidCredentialsError,
    NetworkError,
)


class TestGmailAppPasswordManager:
    """Test cases for GmailAppPasswordManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = GmailAppPasswordManager()
        self.valid_config = {
            "gmail_app_password": "abcd efgh ijkl mnop",
            "gmail_sender_email": "test@gmail.com",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
        }

    def test_initialization(self):
        """Test that manager initializes properly."""
        assert self.manager.provider == AuthenticationProvider.GMAIL_APP_PASSWORD
        assert self.manager.is_authenticated is False
        assert self.manager._logger is not None

    def test_set_configuration_valid(self):
        """Test setting valid configuration."""
        self.manager.set_configuration(self.valid_config)

        config = self.manager.get_configuration()
        assert config["gmail_app_password"] == "abcd efgh ijkl mnop"
        assert config["gmail_sender_email"] == "test@gmail.com"
        assert config["smtp_server"] == "smtp.gmail.com"
        assert config["smtp_port"] == 587

    def test_validate_configuration_valid(self):
        """Test validation of valid configuration."""
        self.manager.set_configuration(self.valid_config)
        assert self.manager.validate_configuration() is True

    def test_validate_configuration_missing_password(self):
        """Test validation with missing app password."""
        config = self.valid_config.copy()
        del config["gmail_app_password"]
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_configuration_missing_email(self):
        """Test validation with missing sender email."""
        config = self.valid_config.copy()
        del config["gmail_sender_email"]
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_configuration_invalid_email_format(self):
        """Test validation with invalid email format."""
        config = self.valid_config.copy()
        config["gmail_sender_email"] = "invalid-email"
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_configuration_non_gmail_email(self):
        """Test validation with non-Gmail email."""
        config = self.valid_config.copy()
        config["gmail_sender_email"] = "test@outlook.com"
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_configuration_invalid_password_format(self):
        """Test validation with invalid app password format."""
        config = self.valid_config.copy()
        config["gmail_app_password"] = "invalid-password"
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is False

    def test_validate_configuration_default_smtp_settings(self):
        """Test validation with default SMTP settings."""
        config = {
            "gmail_app_password": "abcd efgh ijkl mnop",
            "gmail_sender_email": "test@gmail.com",
        }
        self.manager.set_configuration(config)

        assert self.manager.validate_configuration() is True

        # Should set default SMTP settings
        full_config = self.manager.get_configuration()
        assert full_config["smtp_server"] == "smtp.gmail.com"
        assert full_config["smtp_port"] == 587

    def test_validate_email_format_valid(self):
        """Test email format validation with valid emails."""
        valid_emails = [
            "test@gmail.com",
            "user.name@gmail.com",
            "user+tag@gmail.com",
            "user123@gmail.com",
        ]

        for email in valid_emails:
            assert self.manager._is_valid_email(email) is True

    def test_validate_email_format_invalid(self):
        """Test email format validation with invalid emails."""
        invalid_emails = [
            "invalid-email",
            "@gmail.com",
            "test@",
            "test..test@gmail.com",
            "test@gmail",
            "",
        ]

        for email in invalid_emails:
            assert self.manager._is_valid_email(email) is False

    def test_validate_gmail_domain_valid(self):
        """Test Gmail domain validation with valid Gmail addresses."""
        valid_emails = ["test@gmail.com", "user@googlemail.com"]

        for email in valid_emails:
            assert self.manager._is_gmail_domain(email) is True

    def test_validate_gmail_domain_invalid(self):
        """Test Gmail domain validation with non-Gmail addresses."""
        invalid_emails = [
            "test@outlook.com",
            "user@yahoo.com",
            "admin@company.com",
            "test@gmail.co.uk",
            "invalid-email",
        ]

        for email in invalid_emails:
            assert self.manager._is_gmail_domain(email) is False

    def test_validate_app_password_format_valid(self):
        """Test app password format validation with valid passwords."""
        valid_passwords = [
            "abcd efgh ijkl mnop",
            "ABCD EFGH IJKL MNOP",
            "abcdefghijklmnop",
            "ABCDEFGHIJKLMNOP",
            "1234 5678 9012 3456",
        ]

        for password in valid_passwords:
            assert self.manager._is_valid_app_password(password) is True

    def test_validate_app_password_format_invalid(self):
        """Test app password format validation with invalid passwords."""
        invalid_passwords = [
            "short",
            "toolongpasswordthatexceedslimit",
            "abcd-efgh-ijkl-mnop",  # Wrong separator
            "abcd efgh ijkl",  # Too short
            "abcd efgh ijkl mnop qrst",  # Too long
            "",
            "abcd efgh ijkl mn@p",  # Invalid character
        ]

        for password in invalid_passwords:
            assert self.manager._is_valid_app_password(password) is False

    @patch("smtplib.SMTP")
    def test_authenticate_success(self, mock_smtp_class):
        """Test successful authentication."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.starttls.return_value = None
        mock_smtp.login.return_value = None
        mock_smtp.quit.return_value = None

        # Set configuration with credentials
        config_with_credentials = {
            **self.valid_config,
            "gmail_app_password": "abcd efgh ijkl mnop",
            "gmail_sender_email": "test@gmail.com",
        }
        self.manager.set_configuration(config_with_credentials)

        result = self.manager.authenticate()

        assert result is True
        assert self.manager.is_authenticated is True

        # Verify SMTP connection was attempted
        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@gmail.com", "abcd efgh ijkl mnop")
        mock_smtp.quit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_authenticate_smtp_connection_failure(self, mock_smtp_class):
        """Test authentication failure due to SMTP connection error."""
        mock_smtp_class.side_effect = socket.error("Connection failed")

        # Set configuration with credentials
        config_with_credentials = {
            **self.valid_config,
            "gmail_app_password": "abcd efgh ijkl mnop",
            "gmail_sender_email": "test@gmail.com",
        }
        self.manager.set_configuration(config_with_credentials)

        with pytest.raises(NetworkError) as exc_info:
            self.manager.authenticate()

        assert "SMTP connection failed" in str(exc_info.value)
        assert self.manager.is_authenticated is False

    @patch("smtplib.SMTP")
    def test_authenticate_login_failure(self, mock_smtp_class):
        """Test authentication failure due to login error."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.starttls.return_value = None
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Invalid credentials"
        )
        mock_smtp.quit.return_value = None

        # Set configuration with credentials (use properly formatted but wrong password)
        config_with_credentials = {
            **self.valid_config,
            "gmail_app_password": "wrongpassword123",  # 16 chars, properly formatted but wrong
            "gmail_sender_email": "test@gmail.com",
        }
        self.manager.set_configuration(config_with_credentials)

        with pytest.raises(InvalidCredentialsError) as exc_info:
            self.manager.authenticate()

        assert "Invalid Gmail app password" in str(exc_info.value)
        assert self.manager.is_authenticated is False

    def test_authenticate_missing_credentials(self):
        """Test authentication with missing credentials."""
        # Set configuration with missing password
        config_missing_password = {
            **self.valid_config,
            "gmail_sender_email": "test@gmail.com",
            # Missing gmail_app_password
        }
        self.manager.set_configuration(config_missing_password)

        with pytest.raises(InvalidCredentialsError):
            self.manager.authenticate()

    def test_get_access_token_authenticated(self):
        """Test getting access token when authenticated."""
        self.manager.set_configuration(self.valid_config)
        self.manager.is_authenticated = True

        token = self.manager.get_access_token()

        # For app passwords, the token is the password itself
        assert token == "abcd efgh ijkl mnop"

    def test_get_access_token_not_authenticated(self):
        """Test getting access token when not authenticated."""
        self.manager.set_configuration(self.valid_config)

        with pytest.raises(AuthenticationError) as exc_info:
            self.manager.get_access_token()

        assert "Not authenticated" in str(exc_info.value)

    def test_is_token_valid_with_valid_token(self):
        """Test token validation with valid token."""
        self.manager.set_configuration(self.valid_config)

        result = self.manager.is_token_valid("abcd efgh ijkl mnop")
        assert result is True

    def test_is_token_valid_with_invalid_token(self):
        """Test token validation with invalid tokens."""
        self.manager.set_configuration(self.valid_config)

        invalid_tokens = [None, "", "   ", "invalid-token"]

        for token in invalid_tokens:
            result = self.manager.is_token_valid(token)
            assert result is False

    def test_is_token_valid_from_config(self):
        """Test token validation using configured password."""
        self.manager.set_configuration(self.valid_config)
        self.manager.is_authenticated = True

        result = self.manager.is_token_valid()
        assert result is True

    def test_refresh_token_not_supported(self):
        """Test that token refresh is not supported for app passwords."""
        self.manager.set_configuration(self.valid_config)

        with pytest.raises(AuthenticationError) as exc_info:
            self.manager.refresh_token()

        assert "Gmail App Passwords cannot be refreshed" in str(exc_info.value)

    def test_get_smtp_auth_string_with_token(self):
        """Test SMTP auth string generation with provided token."""
        username = "test@gmail.com"
        token = "abcd efgh ijkl mnop"

        auth_string = self.manager.get_smtp_auth_string(username, token)

        # Should return base64-encoded username:password
        expected = "dGVzdEBnbWFpbC5jb206YWJjZCBlZmdoIGlqa2wgbW5vcA=="
        assert auth_string == expected

    def test_get_smtp_auth_string_without_token(self):
        """Test SMTP auth string generation without provided token."""
        self.manager.set_configuration(self.valid_config)
        self.manager.is_authenticated = True

        username = "test@gmail.com"
        auth_string = self.manager.get_smtp_auth_string(username)

        # Should return base64-encoded username:password
        expected = "dGVzdEBnbWFpbC5jb206YWJjZCBlZmdoIGlqa2wgbW5vcA=="
        assert auth_string == expected

    def test_get_smtp_auth_string_no_token_not_authenticated(self):
        """Test SMTP auth string generation without token when not authenticated."""
        # Use configuration without app password
        config_without_password = {
            "gmail_sender_email": "test@gmail.com",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
        }
        self.manager.set_configuration(config_without_password)

        username = "test@gmail.com"

        with pytest.raises(AuthenticationError) as exc_info:
            self.manager.get_smtp_auth_string(username)

        assert "No app password available" in str(exc_info.value)

    @patch("smtplib.SMTP")
    def test_test_smtp_connection_success(self, mock_smtp_class):
        """Test successful SMTP connection test."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.starttls.return_value = None
        mock_smtp.login.return_value = None
        mock_smtp.quit.return_value = None

        result = self.manager._test_smtp_connection(
            "smtp.gmail.com", 587, "test@gmail.com", "password"
        )

        assert result is True
        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@gmail.com", "password")
        mock_smtp.quit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_test_smtp_connection_failure(self, mock_smtp_class):
        """Test SMTP connection test failure."""
        mock_smtp_class.side_effect = socket.error("Connection failed")

        result = self.manager._test_smtp_connection(
            "smtp.gmail.com", 587, "test@gmail.com", "password"
        )

        assert result is False

    @patch("smtplib.SMTP")
    def test_test_smtp_connection_auth_failure(self, mock_smtp_class):
        """Test SMTP connection test with authentication failure."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.starttls.return_value = None
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Invalid credentials"
        )
        mock_smtp.quit.return_value = None

        result = self.manager._test_smtp_connection(
            "smtp.gmail.com", 587, "test@gmail.com", "wrong-password"
        )

        assert result is False

    def test_logout(self):
        """Test logout functionality."""
        self.manager.set_configuration(self.valid_config)
        self.manager.is_authenticated = True

        self.manager.logout()

        assert self.manager.is_authenticated is False

    def test_get_authentication_status_authenticated(self):
        """Test authentication status when authenticated."""
        self.manager.set_configuration(self.valid_config)
        self.manager.is_authenticated = True

        status = self.manager.get_authentication_status()

        assert status["is_authenticated"] is True
        assert status["provider"] == "gmail_app_password"
        assert "last_authentication_time" in status

    def test_get_authentication_status_not_authenticated(self):
        """Test authentication status when not authenticated."""
        status = self.manager.get_authentication_status()

        assert status["is_authenticated"] is False
        assert status["provider"] == "gmail_app_password"
        assert status["last_authentication_time"] is None


class TestGmailAppPasswordManagerIntegration:
    """Integration tests for GmailAppPasswordManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = GmailAppPasswordManager()
        self.valid_config = {
            "gmail_app_password": "abcd efgh ijkl mnop",
            "gmail_sender_email": "test@gmail.com",
        }

    @patch("smtplib.SMTP")
    def test_full_authentication_workflow(self, mock_smtp_class):
        """Test complete authentication workflow."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.starttls.return_value = None
        mock_smtp.login.return_value = None
        mock_smtp.quit.return_value = None

        # Set configuration
        self.manager.set_configuration(self.valid_config)
        assert self.manager.validate_configuration() is True

        # Authenticate - set configuration with credentials
        config_with_credentials = {
            **self.valid_config,
            "gmail_app_password": "abcd efgh ijkl mnop",
            "gmail_sender_email": "test@gmail.com",
        }
        self.manager.set_configuration(config_with_credentials)

        result = self.manager.authenticate()
        assert result is True

        # Get access token
        token = self.manager.get_access_token()
        assert token == "abcd efgh ijkl mnop"

        # Validate token
        assert self.manager.is_token_valid(token) is True

        # Get SMTP auth string
        auth_string = self.manager.get_smtp_auth_string("test@gmail.com")
        # Should return base64-encoded username:password
        expected = "dGVzdEBnbWFpbC5jb206YWJjZCBlZmdoIGlqa2wgbW5vcA=="
        assert auth_string == expected

        # Check authentication status
        status = self.manager.get_authentication_status()
        assert status["is_authenticated"] is True

        # Logout
        self.manager.logout()
        status = self.manager.get_authentication_status()
        assert status["is_authenticated"] is False

    def test_configuration_validation_edge_cases(self):
        """Test configuration validation with various edge cases."""
        # Test with minimal valid configuration
        minimal_config = {
            "gmail_app_password": "abcd efgh ijkl mnop",
            "gmail_sender_email": "test@gmail.com",
        }

        self.manager.set_configuration(minimal_config)
        assert self.manager.validate_configuration() is True

        # Should set default SMTP settings
        full_config = self.manager.get_configuration()
        assert full_config["smtp_server"] == "smtp.gmail.com"
        assert full_config["smtp_port"] == 587

        # Test with custom SMTP settings
        custom_config = minimal_config.copy()
        custom_config.update({"smtp_server": "custom.gmail.com", "smtp_port": 465})

        self.manager.set_configuration(custom_config)
        assert self.manager.validate_configuration() is True

        full_config = self.manager.get_configuration()
        assert full_config["smtp_server"] == "custom.gmail.com"
        assert full_config["smtp_port"] == 465

    @patch("smtplib.SMTP")
    def test_error_handling_scenarios(self, mock_smtp_class):
        """Test various error handling scenarios."""
        # Set configuration with credentials
        config_with_credentials = {
            **self.valid_config,
            "gmail_app_password": "abcd efgh ijkl mnop",
            "gmail_sender_email": "test@gmail.com",
        }
        self.manager.set_configuration(config_with_credentials)

        # Test network error
        mock_smtp_class.side_effect = socket.timeout("Connection timeout")

        with pytest.raises(NetworkError):
            self.manager.authenticate()

        # Test authentication error
        mock_smtp = Mock()
        mock_smtp_class.side_effect = None
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.starttls.return_value = None
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Invalid credentials"
        )
        mock_smtp.quit.return_value = None

        with pytest.raises(InvalidCredentialsError):
            self.manager.authenticate()

        # Test general SMTP error
        mock_smtp.login.side_effect = smtplib.SMTPException("General SMTP error")

        with pytest.raises(AuthenticationError):
            self.manager.authenticate()

    def test_password_format_variations(self):
        """Test various valid app password formats."""
        password_formats = [
            "abcd efgh ijkl mnop",  # Standard format with spaces
            "abcdefghijklmnop",  # No spaces
            "ABCD EFGH IJKL MNOP",  # Uppercase with spaces
            "ABCDEFGHIJKLMNOP",  # Uppercase no spaces
            "1234 5678 9012 3456",  # Numeric
        ]

        for password in password_formats:
            config = {
                "gmail_app_password": password,
                "gmail_sender_email": "test@gmail.com",
            }

            self.manager.set_configuration(config)
            assert self.manager.validate_configuration() is True

            # Test token validation
            assert self.manager.is_token_valid(password) is True