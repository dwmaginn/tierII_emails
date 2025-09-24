"""Unit tests for MailerSend authentication manager.

This module contains comprehensive tests for the MailerSendManager class,
following TDD principles. Tests are written first to define expected behavior
before implementation.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import time

from src.auth.base_authentication_manager import (
    BaseAuthenticationManager,
    AuthenticationProvider,
    AuthenticationError,
    InvalidCredentialsError,
    NetworkError,
)


class TestMailerSendManagerInitialization:
    """Test suite for MailerSendManager initialization."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for MailerSend configuration."""
        settings = Mock()
        settings.mailersend_api_token = "ms_test_api_key_12345"
        settings.sender_email = "test@example.com"
        settings.sender_name = "Test Sender"
        return settings

    @pytest.fixture
    def mailersend_manager(self, mock_settings):
        """Create MailerSendManager instance for testing."""
        from src.auth.mailersend_manager import MailerSendManager
        return MailerSendManager(mock_settings)

    def test_mailersend_manager_initialization_success(self, mock_settings):
        """Test MailerSendManager initialization with valid settings."""
        from src.auth.mailersend_manager import MailerSendManager
        
        manager = MailerSendManager(mock_settings)
        
        assert manager.provider == AuthenticationProvider.MAILERSEND
        assert manager.settings == mock_settings
        assert manager._api_key == "ms_test_api_key_12345"
        assert manager._client is not None
        assert manager.is_authenticated is False
        assert manager.last_authenticated is None

    def test_mailersend_manager_missing_api_key(self):
        """Test MailerSendManager initialization fails with missing API key."""
        from src.auth.mailersend_manager import MailerSendManager
        
        settings = Mock()
        settings.mailersend_api_token = None
        
        with pytest.raises(InvalidCredentialsError) as exc_info:
            MailerSendManager(settings)
        
        assert "MailerSend API key is required" in str(exc_info.value)
        assert exc_info.value.provider == AuthenticationProvider.MAILERSEND
        assert exc_info.value.error_code == "MISSING_API_KEY"

    def test_mailersend_manager_empty_api_key(self):
        """Test MailerSendManager initialization fails with empty API key."""
        from src.auth.mailersend_manager import MailerSendManager
        
        settings = Mock()
        settings.mailersend_api_token = ""
        
        with pytest.raises(InvalidCredentialsError) as exc_info:
            MailerSendManager(settings)
        
        assert "MailerSend API key is required" in str(exc_info.value)

    def test_mailersend_manager_whitespace_api_key(self):
        """Test MailerSendManager initialization fails with whitespace-only API key."""
        from src.auth.mailersend_manager import MailerSendManager
        
        settings = Mock()
        settings.mailersend_api_token = "   "
        
        with pytest.raises(InvalidCredentialsError) as exc_info:
            MailerSendManager(settings)
        
        assert "MailerSend API key is required" in str(exc_info.value)

    def test_mailersend_manager_invalid_settings_object(self):
        """Test MailerSendManager initialization with invalid settings object."""
        from src.auth.mailersend_manager import MailerSendManager
        
        with pytest.raises(InvalidCredentialsError):
            MailerSendManager(None)

    @patch('src.auth.mailersend_manager.MailerSendClient')
    def test_mailersend_manager_client_initialization_failure(self, mock_client_class, mock_settings):
        """Test MailerSendManager initialization fails when client setup fails."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_client_class.side_effect = Exception("Network connectivity issue")
        
        with pytest.raises(InvalidCredentialsError) as exc_info:
            MailerSendManager(mock_settings)
        
        assert "Failed to initialize MailerSend client" in str(exc_info.value)
        assert exc_info.value.error_code == "CLIENT_INIT_ERROR"

    def test_mailersend_manager_malformed_api_token(self):
        """Test MailerSendManager initialization with malformed API token format."""
        from src.auth.mailersend_manager import MailerSendManager
        
        settings = Mock()
        settings.mailersend_api_token = "invalid_format_token"
        settings.sender_email = "test@example.com"
        
        # Should still initialize but may fail during authentication
        manager = MailerSendManager(settings)
        assert manager._api_key == "invalid_format_token"


class TestMailerSendManagerAuthentication:
    """Test suite for MailerSend authentication methods."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for MailerSend configuration."""
        settings = Mock()
        settings.mailersend_api_token = "ms_test_api_key_12345"
        settings.sender_email = "test@example.com"
        settings.sender_name = "Test Sender"
        return settings

    @pytest.fixture
    def mailersend_manager(self, mock_settings):
        """Create MailerSendManager instance for testing."""
        from src.auth.mailersend_manager import MailerSendManager
        return MailerSendManager(mock_settings)

    def test_authenticate_success(self, mailersend_manager):
        """Test successful authentication with MailerSend API."""
        with patch.object(mailersend_manager._client.tokens, 'list_tokens') as mock_list_tokens:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_list_tokens.return_value = mock_response
            
            result = mailersend_manager.authenticate()
            
            assert result is True
            assert mailersend_manager.is_authenticated is True
            assert mailersend_manager.last_authenticated is not None
            assert isinstance(mailersend_manager.last_authenticated, datetime)

    def test_authenticate_invalid_api_key_401(self, mailersend_manager):
        """Test authentication failure with invalid API key (401 response)."""
        with patch.object(mailersend_manager._client.tokens, 'list_tokens') as mock_list_tokens:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"message": "Invalid API key"}
            mock_list_tokens.return_value = mock_response
            
            with pytest.raises(InvalidCredentialsError) as exc_info:
                mailersend_manager.authenticate()
            
            assert "Invalid MailerSend API key" in str(exc_info.value)
            assert exc_info.value.provider == AuthenticationProvider.MAILERSEND
            assert exc_info.value.error_code == "INVALID_API_KEY"
            assert mailersend_manager.is_authenticated is False

    def test_authenticate_network_timeout(self, mailersend_manager):
        """Test authentication failure due to network timeout."""
        with patch.object(mailersend_manager._client.tokens, 'list_tokens') as mock_list_tokens:
            mock_list_tokens.side_effect = Exception("Network timeout")
            
            with pytest.raises(NetworkError) as exc_info:
                mailersend_manager.authenticate()
            
            assert "Network error during MailerSend authentication" in str(exc_info.value)
            assert exc_info.value.provider == AuthenticationProvider.MAILERSEND
            assert exc_info.value.error_code == "NETWORK_ERROR"

    def test_authenticate_rate_limiting_429(self, mailersend_manager):
        """Test authentication failure due to rate limiting (429 response)."""
        with patch.object(mailersend_manager._client.tokens, 'list_tokens') as mock_list_tokens:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {"message": "Rate limit exceeded"}
            mock_list_tokens.return_value = mock_response
            
            with pytest.raises(NetworkError) as exc_info:
                mailersend_manager.authenticate()
            
            assert "Network error during MailerSend authentication" in str(exc_info.value)
            assert exc_info.value.error_code == "NETWORK_ERROR"

    def test_authenticate_malformed_api_response(self, mailersend_manager):
        """Test authentication failure with malformed API response."""
        with patch.object(mailersend_manager._client.tokens, 'list_tokens') as mock_list_tokens:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_list_tokens.return_value = mock_response
            
            with pytest.raises(NetworkError) as exc_info:
                mailersend_manager.authenticate()
            
            assert "Network error during MailerSend authentication" in str(exc_info.value)
            assert exc_info.value.error_code == "NETWORK_ERROR"

    def test_get_access_token_authenticated(self, mailersend_manager):
        """Test get_access_token returns API key when authenticated."""
        mailersend_manager.is_authenticated = True
        
        token = mailersend_manager.get_access_token()
        
        assert token == "ms_test_api_key_12345"

    def test_get_access_token_not_authenticated(self, mailersend_manager):
        """Test get_access_token raises error when not authenticated."""
        mailersend_manager.is_authenticated = False
        
        with pytest.raises(AuthenticationError) as exc_info:
            mailersend_manager.get_access_token()
        
        assert "Not authenticated with MailerSend" in str(exc_info.value)
        assert exc_info.value.error_code == "NOT_AUTHENTICATED"

    def test_is_token_valid_authenticated(self, mailersend_manager):
        """Test is_token_valid returns True when authenticated with valid token."""
        mailersend_manager.is_authenticated = True
        
        result = mailersend_manager.is_token_valid()
        
        assert result is True

    def test_is_token_valid_not_authenticated(self, mailersend_manager):
        """Test is_token_valid returns False when not authenticated."""
        mailersend_manager.is_authenticated = False
        
        result = mailersend_manager.is_token_valid()
        
        assert result is False

    def test_refresh_token_with_valid_key(self, mailersend_manager):
        """Test refresh_token returns True with valid API key."""
        mailersend_manager.is_authenticated = True
        
        result = mailersend_manager.refresh_token()
        
        assert result is True


class TestMailerSendManagerConfigurationValidation:
    """Test suite for MailerSend configuration validation."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for MailerSend configuration."""
        settings = Mock()
        settings.mailersend_api_token = "ms_test_api_key_12345"
        settings.sender_email = "test@example.com"
        settings.sender_name = "Test Sender"
        return settings

    @pytest.fixture
    def mailersend_manager(self, mock_settings):
        """Create MailerSendManager instance for testing."""
        from src.auth.mailersend_manager import MailerSendManager
        return MailerSendManager(mock_settings)

    def test_validate_configuration_success(self, mailersend_manager):
        """Test successful configuration validation with valid settings."""
        result = mailersend_manager.validate_configuration()
        
        assert result is True

    def test_validate_configuration_missing_sender_email(self, mock_settings):
        """Test configuration validation fails with missing sender email."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings.sender_email = None
        manager = MailerSendManager(mock_settings)
        
        result = manager.validate_configuration()
        assert result is False

    def test_validate_configuration_empty_sender_email(self, mock_settings):
        """Test configuration validation fails with empty sender email."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings.sender_email = ""
        manager = MailerSendManager(mock_settings)
        
        result = manager.validate_configuration()
        assert result is False

    def test_validate_configuration_invalid_email_format_no_at(self, mock_settings):
        """Test configuration validation fails with invalid email format (no @)."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings.sender_email = "invalid-email"
        manager = MailerSendManager(mock_settings)
        
        result = manager.validate_configuration()
        assert result is False

    def test_validate_configuration_invalid_email_format_malformed_domain(self, mock_settings):
        """Test configuration validation fails with malformed domain."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings.sender_email = "test@invalid"
        manager = MailerSendManager(mock_settings)
        
        result = manager.validate_configuration()
        assert result is False

    def test_validate_configuration_whitespace_only_email(self, mock_settings):
        """Test configuration validation fails with whitespace-only email."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings.sender_email = "   "
        manager = MailerSendManager(mock_settings)
        
        result = manager.validate_configuration()
        assert result is False

    def test_validate_configuration_exception_handling(self, mock_settings):
        """Test configuration validation handles exceptions gracefully."""
        from src.auth.mailersend_manager import MailerSendManager
        
        # Remove sender_email attribute to cause AttributeError
        delattr(mock_settings, 'sender_email')
        manager = MailerSendManager(mock_settings)
        
        result = manager.validate_configuration()
        assert result is False

    def test_is_valid_email_valid_formats(self, mailersend_manager):
        """Test _is_valid_email method with valid email formats."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.com",
            "test_user@sub.domain.com"
        ]
        
        for email in valid_emails:
            assert mailersend_manager._is_valid_email(email) is True

    def test_is_valid_email_invalid_formats(self, mailersend_manager):
        """Test _is_valid_email method with invalid email formats."""
        invalid_emails = [
            "",
            None,
            "invalid",
            "@domain.com",
            "user@",
            "user@domain"
        ]
        
        for email in invalid_emails:
            assert mailersend_manager._is_valid_email(email) is False


class TestMailerSendManagerEmailSending:
    """Test suite for MailerSend email sending functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for MailerSend configuration."""
        settings = Mock()
        settings.mailersend_api_token = "ms_test_api_key_12345"
        settings.sender_email = "test@example.com"
        settings.sender_name = "Test Sender"
        return settings

    @pytest.fixture
    def mailersend_manager(self, mock_settings):
        """Create MailerSendManager instance for testing."""
        from src.auth.mailersend_manager import MailerSendManager
        return MailerSendManager(mock_settings)

    def test_send_email_success_with_text_content(self, mailersend_manager):
        """Test successful email sending with provided text content."""
        mailersend_manager.is_authenticated = True
        
        with patch.object(mailersend_manager, '_send_via_mailersend') as mock_send:
            mock_send.return_value = True
            
            result = mailersend_manager.send_email(
                to_email="recipient@example.com",
                to_name="Recipient Name",
                subject="Test Subject",
                html_content="<h1>Test HTML</h1>",
                text_content="Test Text"
            )
            
            assert result is True
            mock_send.assert_called_once_with(
                to_email="recipient@example.com",
                to_name="Recipient Name",
                subject="Test Subject",
                html_content="<h1>Test HTML</h1>",
                text_content="Test Text"
            )

    def test_send_email_success_auto_generated_text(self, mailersend_manager):
        """Test successful email sending with auto-generated text content."""
        mailersend_manager.is_authenticated = True
        
        with patch.object(mailersend_manager, '_send_via_mailersend') as mock_send, \
             patch.object(mailersend_manager, '_html_to_text') as mock_html_to_text:
            mock_send.return_value = True
            mock_html_to_text.return_value = "Generated text content"
            
            result = mailersend_manager.send_email(
                to_email="recipient@example.com",
                to_name="Recipient Name",
                subject="Test Subject",
                html_content="<h1>Test HTML</h1>"
            )
            
            assert result is True
            mock_html_to_text.assert_called_once_with("<h1>Test HTML</h1>")
            mock_send.assert_called_once()

    def test_send_email_not_authenticated(self, mailersend_manager):
        """Test email sending fails when not authenticated."""
        mailersend_manager.is_authenticated = False
        
        with pytest.raises(AuthenticationError) as exc_info:
            mailersend_manager.send_email(
                to_email="recipient@example.com",
                to_name="Recipient Name",
                subject="Test Subject",
                html_content="<h1>Test HTML</h1>"
            )
        
        assert "Not authenticated with MailerSend" in str(exc_info.value)
        assert exc_info.value.error_code == "NOT_AUTHENTICATED"

    def test_send_email_empty_recipient_email(self, mailersend_manager):
        """Test email sending fails with empty recipient email."""
        mailersend_manager.is_authenticated = True
        
        with pytest.raises(ValueError) as exc_info:
            mailersend_manager.send_email(
                to_email="",
                to_name="Recipient Name",
                subject="Test Subject",
                html_content="<h1>Test HTML</h1>"
            )
        
        assert "Recipient email is required" in str(exc_info.value)

    def test_send_email_missing_subject(self, mailersend_manager):
        """Test email sending fails with missing subject."""
        mailersend_manager.is_authenticated = True
        
        with pytest.raises(ValueError) as exc_info:
            mailersend_manager.send_email(
                to_email="recipient@example.com",
                to_name="Recipient Name",
                subject="",
                html_content="<h1>Test HTML</h1>"
            )
        
        assert "Email subject is required" in str(exc_info.value)

    def test_send_email_missing_html_content(self, mailersend_manager):
        """Test email sending fails with missing HTML content."""
        mailersend_manager.is_authenticated = True
        
        with pytest.raises(ValueError) as exc_info:
            mailersend_manager.send_email(
                to_email="recipient@example.com",
                to_name="Recipient Name",
                subject="Test Subject",
                html_content=""
            )
        
        assert "Email content is required" in str(exc_info.value)

    def test_send_email_invalid_recipient_format(self, mailersend_manager):
        """Test email sending with invalid recipient email format."""
        mailersend_manager.is_authenticated = True
        
        with patch.object(mailersend_manager, '_send_via_mailersend') as mock_send:
            mock_send.side_effect = AuthenticationError(
                "Invalid email format",
                AuthenticationProvider.MAILERSEND,
                "VALIDATION_ERROR"
            )
            
            with pytest.raises(AuthenticationError):
                mailersend_manager.send_email(
                    to_email="invalid-email",
                    to_name="Recipient Name",
                    subject="Test Subject",
                    html_content="<h1>Test HTML</h1>"
                )

    def test_send_email_api_error_400(self, mailersend_manager):
        """Test email sending handles API 400 error."""
        mailersend_manager.is_authenticated = True
        
        with patch.object(mailersend_manager, '_send_via_mailersend') as mock_send:
            mock_send.side_effect = AuthenticationError(
                "Bad request",
                AuthenticationProvider.MAILERSEND,
                "SEND_ERROR_400"
            )
            
            with pytest.raises(AuthenticationError):
                mailersend_manager.send_email(
                    to_email="recipient@example.com",
                    to_name="Recipient Name",
                    subject="Test Subject",
                    html_content="<h1>Test HTML</h1>"
                )

    def test_send_email_api_error_403(self, mailersend_manager):
        """Test email sending handles API 403 error."""
        mailersend_manager.is_authenticated = True
        
        with patch.object(mailersend_manager, '_send_via_mailersend') as mock_send:
            mock_send.side_effect = AuthenticationError(
                "Forbidden",
                AuthenticationProvider.MAILERSEND,
                "SEND_ERROR_403"
            )
            
            with pytest.raises(AuthenticationError):
                mailersend_manager.send_email(
                    to_email="recipient@example.com",
                    to_name="Recipient Name",
                    subject="Test Subject",
                    html_content="<h1>Test HTML</h1>"
                )

    def test_send_email_api_error_422(self, mailersend_manager):
        """Test email sending handles API 422 error."""
        mailersend_manager.is_authenticated = True
        
        with patch.object(mailersend_manager, '_send_via_mailersend') as mock_send:
            mock_send.side_effect = AuthenticationError(
                "Unprocessable entity",
                AuthenticationProvider.MAILERSEND,
                "SEND_ERROR_422"
            )
            
            with pytest.raises(AuthenticationError):
                mailersend_manager.send_email(
                    to_email="recipient@example.com",
                    to_name="Recipient Name",
                    subject="Test Subject",
                    html_content="<h1>Test HTML</h1>"
                )

    def test_send_email_api_error_500(self, mailersend_manager):
        """Test email sending handles API 500 error."""
        mailersend_manager.is_authenticated = True
        
        with patch.object(mailersend_manager, '_send_via_mailersend') as mock_send:
            mock_send.side_effect = AuthenticationError(
                "Internal server error",
                AuthenticationProvider.MAILERSEND,
                "SEND_ERROR_500"
            )
            
            with pytest.raises(AuthenticationError):
                mailersend_manager.send_email(
                    to_email="recipient@example.com",
                    to_name="Recipient Name",
                    subject="Test Subject",
                    html_content="<h1>Test HTML</h1>"
                )

    def test_send_email_network_failure(self, mailersend_manager):
        """Test email sending handles network failures."""
        mailersend_manager.is_authenticated = True
        
        with patch.object(mailersend_manager, '_send_via_mailersend') as mock_send:
            mock_send.side_effect = AuthenticationError(
                "Network error",
                AuthenticationProvider.MAILERSEND,
                "SEND_ERROR"
            )
            
            with pytest.raises(AuthenticationError):
                mailersend_manager.send_email(
                    to_email="recipient@example.com",
                    to_name="Recipient Name",
                    subject="Test Subject",
                    html_content="<h1>Test HTML</h1>"
                )


class TestMailerSendManagerInternalMethods:
    """Test suite for MailerSend internal methods."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for MailerSend configuration."""
        settings = Mock()
        settings.mailersend_api_token = "ms_test_api_key_12345"
        settings.sender_email = "test@example.com"
        settings.sender_name = "Test Sender"
        return settings

    @pytest.fixture
    def mailersend_manager(self, mock_settings):
        """Create MailerSendManager instance for testing."""
        from src.auth.mailersend_manager import MailerSendManager
        return MailerSendManager(mock_settings)

    def test_send_via_mailersend_success(self, mailersend_manager):
        """Test internal _send_via_mailersend method success."""
        with patch('src.auth.mailersend_manager.EmailBuilder') as mock_email_builder:
            mock_email = Mock()
            mock_builder = Mock()
            mock_builder.from_email.return_value = mock_builder
            mock_builder.to_many.return_value = mock_builder
            mock_builder.subject.return_value = mock_builder
            mock_builder.html.return_value = mock_builder
            mock_builder.text.return_value = mock_builder
            mock_builder.build.return_value = mock_email
            mock_email_builder.return_value = mock_builder
            
            with patch.object(mailersend_manager._client.emails, 'send') as mock_send:
                mock_response = Mock()
                mock_response.status_code = 202
                mock_send.return_value = mock_response
                
                result = mailersend_manager._send_via_mailersend(
                    to_email="recipient@example.com",
                    to_name="Recipient Name",
                    subject="Test Subject",
                    html_content="<h1>Test HTML</h1>",
                    text_content="Test Text"
                )
                
                assert result is True
                mock_builder.from_email.assert_called_once_with("test@example.com", "Test Sender")
                mock_builder.to_many.assert_called_once_with([{"email": "recipient@example.com", "name": "Recipient Name"}])

    def test_send_via_mailersend_api_error_with_message(self, mailersend_manager):
        """Test _send_via_mailersend handles API errors with detailed messages."""
        with patch('src.auth.mailersend_manager.EmailBuilder') as mock_email_builder:
            mock_email = Mock()
            mock_builder = Mock()
            mock_builder.from_email.return_value = mock_builder
            mock_builder.to_many.return_value = mock_builder
            mock_builder.subject.return_value = mock_builder
            mock_builder.html.return_value = mock_builder
            mock_builder.text.return_value = mock_builder
            mock_builder.build.return_value = mock_email
            mock_email_builder.return_value = mock_builder
            
            with patch.object(mailersend_manager._client.emails, 'send') as mock_send:
                mock_response = Mock()
                mock_response.status_code = 422
                mock_response.json.return_value = {"message": "Validation failed"}
                mock_send.return_value = mock_response
                
                with pytest.raises(AuthenticationError) as exc_info:
                    mailersend_manager._send_via_mailersend(
                        to_email="recipient@example.com",
                        to_name="Recipient Name",
                        subject="Test Subject",
                        html_content="<h1>Test HTML</h1>",
                        text_content="Test Text"
                    )
                
                assert "Failed to send email: HTTP 422 - Validation failed" in str(exc_info.value)

    def test_send_via_mailersend_exception_handling(self, mailersend_manager):
        """Test _send_via_mailersend handles general exceptions."""
        with patch('src.auth.mailersend_manager.EmailBuilder') as mock_email_builder:
            mock_email_builder.side_effect = Exception("EmailBuilder error")
            
            with pytest.raises(AuthenticationError) as exc_info:
                mailersend_manager._send_via_mailersend(
                    to_email="recipient@example.com",
                    to_name="Recipient Name",
                    subject="Test Subject",
                    html_content="<h1>Test HTML</h1>",
                    text_content="Test Text"
                )
            
            assert "Error sending email via MailerSend" in str(exc_info.value)
            assert exc_info.value.error_code == "SEND_ERROR"


class TestMailerSendManagerHTMLToText:
    """Test suite for HTML to text conversion functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for MailerSend configuration."""
        settings = Mock()
        settings.mailersend_api_token = "ms_test_api_key_12345"
        settings.sender_email = "test@example.com"
        settings.sender_name = "Test Sender"
        return settings

    @pytest.fixture
    def mailersend_manager(self, mock_settings):
        """Create MailerSendManager instance for testing."""
        from src.auth.mailersend_manager import MailerSendManager
        return MailerSendManager(mock_settings)

    def test_html_to_text_simple_tags(self, mailersend_manager):
        """Test HTML to text conversion with simple HTML tags."""
        html_content = "<h1>Hello World</h1><p>This is a <strong>test</strong> email.</p>"
        
        text_content = mailersend_manager._html_to_text(html_content)
        
        assert "Hello World" in text_content
        assert "This is a test email." in text_content
        assert "<h1>" not in text_content
        assert "<p>" not in text_content
        assert "<strong>" not in text_content

    def test_html_to_text_html_entities(self, mailersend_manager):
        """Test HTML to text conversion with HTML entities."""
        html_content = "<p>Price: $100 &amp; up. &lt;Special&gt; &quot;Offer&quot; &#39;Today&#39; &nbsp;</p>"
        
        text_content = mailersend_manager._html_to_text(html_content)
        
        assert "$100 & up" in text_content
        assert "<Special>" in text_content
        assert '"Offer"' in text_content
        assert "'Today'" in text_content
        assert "&amp;" not in text_content
        assert "&lt;" not in text_content
        assert "&quot;" not in text_content

    def test_html_to_text_whitespace_normalization(self, mailersend_manager):
        """Test HTML to text conversion normalizes whitespace."""
        html_content = "<p>Multiple    spaces\n\nand\t\ttabs</p>"
        
        text_content = mailersend_manager._html_to_text(html_content)
        
        assert "Multiple spaces and tabs" in text_content
        assert "    " not in text_content
        assert "\n\n" not in text_content
        assert "\t\t" not in text_content

    def test_html_to_text_empty_content(self, mailersend_manager):
        """Test HTML to text conversion with empty content."""
        result = mailersend_manager._html_to_text("")
        assert result == ""
        
        result = mailersend_manager._html_to_text(None)
        assert result == ""

    def test_html_to_text_malformed_html(self, mailersend_manager):
        """Test HTML to text conversion with malformed HTML structure."""
        html_content = "<p>Unclosed paragraph<div>Nested <span>content</div>"
        
        text_content = mailersend_manager._html_to_text(html_content)
        
        assert "Unclosed paragraph" in text_content
        assert "Nested content" in text_content
        assert "<p>" not in text_content
        assert "<div>" not in text_content

    def test_html_to_text_complex_nested_tags(self, mailersend_manager):
        """Test HTML to text conversion with complex nested tags."""
        html_content = """
        <div>
            <h1>Title</h1>
            <ul>
                <li>Item <strong>1</strong></li>
                <li>Item <em>2</em></li>
            </ul>
            <p>Footer <a href="http://example.com">link</a></p>
        </div>
        """
        
        text_content = mailersend_manager._html_to_text(html_content)
        
        assert "Title" in text_content
        assert "Item 1" in text_content
        assert "Item 2" in text_content
        assert "Footer link" in text_content
        assert "<div>" not in text_content
        assert "<ul>" not in text_content
        assert "<li>" not in text_content

    def test_html_to_text_special_characters(self, mailersend_manager):
        """Test HTML to text conversion with special characters."""
        html_content = "<p>Special chars: © ® ™ € £ ¥</p>"
        
        text_content = mailersend_manager._html_to_text(html_content)
        
        assert "Special chars: © ® ™ € £ ¥" in text_content

    def test_html_to_text_conversion_error_fallback(self, mailersend_manager):
        """Test HTML to text conversion graceful fallback on error."""
        html_content = "<p>Valid content</p>"
        
        with patch('re.sub', side_effect=Exception("Regex error")):
            text_content = mailersend_manager._html_to_text(html_content)
            
            # Should return original content on error
            assert text_content == html_content


class TestMailerSendManagerUtilityMethods:
    """Test suite for MailerSend utility methods."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for MailerSend configuration."""
        settings = Mock()
        settings.mailersend_api_token = "ms_test_api_key_12345"
        settings.sender_email = "test@example.com"
        settings.sender_name = "Test Sender"
        return settings

    @pytest.fixture
    def mailersend_manager(self, mock_settings):
        """Create MailerSendManager instance for testing."""
        from src.auth.mailersend_manager import MailerSendManager
        return MailerSendManager(mock_settings)

    def test_get_provider_name(self, mailersend_manager):
        """Test provider name getter."""
        assert mailersend_manager.get_provider_name() == "MailerSend"

    def test_get_authentication_status_not_authenticated(self, mailersend_manager):
        """Test authentication status reporting when not authenticated."""
        status = mailersend_manager.get_authentication_status()
        
        assert status["authenticated"] is False
        assert status["provider"] == "MailerSend"
        assert status["last_authenticated"] is None
        assert status["api_key_configured"] is True

    def test_get_authentication_status_authenticated(self, mailersend_manager):
        """Test authentication status reporting when authenticated."""
        mailersend_manager.is_authenticated = True
        mailersend_manager.last_authenticated = datetime.now()
        
        status = mailersend_manager.get_authentication_status()
        
        assert status["authenticated"] is True
        assert status["provider"] == "MailerSend"
        assert status["last_authenticated"] is not None
        assert isinstance(status["last_authenticated"], datetime)
        assert status["api_key_configured"] is True


class TestMailerSendManagerIntegration:
    """Integration tests for MailerSendManager with other components."""

    def test_integration_with_authentication_factory(self):
        """Test MailerSendManager integration with AuthenticationFactory."""
        from src.auth.authentication_factory import AuthenticationFactory
        from src.auth.mailersend_manager import MailerSendManager
        
        factory = AuthenticationFactory()
        factory.register_provider(AuthenticationProvider.MAILERSEND, MailerSendManager)
        
        config = {
            'mailersend_api_token': 'test_key',
            'sender_email': 'test@example.com'
        }
        
        manager = factory.create_manager(AuthenticationProvider.MAILERSEND, config)
        
        assert isinstance(manager, MailerSendManager)
        assert manager.provider == AuthenticationProvider.MAILERSEND

    def test_performance_requirements(self):
        """Test that MailerSend authentication meets performance requirements."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings = Mock()
        mock_settings.mailersend_api_token = "test_key"
        mock_settings.sender_email = "test@example.com"
        
        mailersend_manager = MailerSendManager(mock_settings)
        
        start_time = time.time()
        
        with patch.object(mailersend_manager._client.tokens, 'list_tokens') as mock_list_tokens:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_list_tokens.return_value = mock_response
            
            mailersend_manager.authenticate()
        
        auth_time = time.time() - start_time
        assert auth_time < 5.0, f"Authentication took {auth_time:.2f}s, should be < 5s"

    def test_performance_requirements_email_sending(self):
        """Test that MailerSend email sending meets performance requirements."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings = Mock()
        mock_settings.mailersend_api_token = "test_key"
        mock_settings.sender_email = "test@example.com"
        
        mailersend_manager = MailerSendManager(mock_settings)
        mailersend_manager.is_authenticated = True
        
        start_time = time.time()
        
        with patch.object(mailersend_manager, '_send_via_mailersend') as mock_send:
            mock_send.return_value = True
            
            mailersend_manager.send_email(
                to_email="test@example.com",
                to_name="Test",
                subject="Test",
                html_content="Test"
            )
        
        send_time = time.time() - start_time
        assert send_time < 2.0, f"Email sending took {send_time:.2f}s, should be < 2s"

    def test_error_handling_with_detailed_messages(self):
        """Test error handling includes detailed error messages."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings = Mock()
        mock_settings.mailersend_api_token = "test_key"
        mock_settings.sender_email = "test@example.com"
        
        mailersend_manager = MailerSendManager(mock_settings)
        mailersend_manager.is_authenticated = True
        
        with patch.object(mailersend_manager, '_send_via_mailersend') as mock_send:
            mock_send.side_effect = AuthenticationError(
                "Validation failed: Invalid email format",
                AuthenticationProvider.MAILERSEND,
                "VALIDATION_ERROR"
            )
            
            with pytest.raises(AuthenticationError) as exc_info:
                mailersend_manager.send_email(
                    to_email="invalid-email",
                    to_name="Test",
                    subject="Test",
                    html_content="Test"
                )
            
            assert "Validation failed" in str(exc_info.value)
            assert exc_info.value.error_code == "VALIDATION_ERROR"


# Mark tests for pytest
pytest.mark.mailersend = pytest.mark.mailersend
pytest.mark.unit = pytest.mark.unit