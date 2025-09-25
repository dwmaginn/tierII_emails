"""Unit tests for MailerSend authentication manager.

This module contains comprehensive tests for the MailerSendManager class,
following TDD principles. Tests are written first to define expected behavior
before implementation.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.auth.base_authentication_manager import (
    BaseAuthenticationManager,
    AuthenticationProvider,
    AuthenticationError,
    InvalidCredentialsError,
    NetworkError,
)


class TestMailerSendManager:
    """Test suite for MailerSendManager class."""

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
        
        manager = MailerSendManager(AuthenticationProvider.MAILERSEND)
        manager.set_configuration({
            'mailersend_api_token': 'ms_test_api_key_12345',
            'sender_email': 'test@example.com',
            'sender_name': 'Test Sender'
        })
        
        # Validate configuration to initialize the manager
        manager.validate_configuration()
        return manager

    def test_mailersend_manager_initialization(self, mock_settings):
        """Test MailerSendManager initialization with valid settings."""
        from src.auth.mailersend_manager import MailerSendManager
        
        manager = MailerSendManager(AuthenticationProvider.MAILERSEND)
        manager.set_configuration({
            'mailersend_api_token': 'ms_test_api_key_12345',
            'sender_email': 'test@example.com',
            'sender_name': 'Test Sender'
        })
        
        # Validate configuration to initialize the manager
        assert manager.validate_configuration() is True
        assert manager.provider == AuthenticationProvider.MAILERSEND
        assert manager._api_key == "ms_test_api_key_12345"
        assert manager._client is not None

    def test_mailersend_manager_missing_api_key(self):
        """Test MailerSendManager initialization fails with missing API key."""
        from src.auth.mailersend_manager import MailerSendManager
        
        manager = MailerSendManager(AuthenticationProvider.MAILERSEND)
        manager.set_configuration({
            'sender_email': 'test@example.com',
            'sender_name': 'Test Sender'
        })
        
        # Should fail validation due to missing API key
        assert manager.validate_configuration() is False

    def test_mailersend_manager_empty_api_key(self):
        """Test MailerSendManager initialization fails with empty API key."""
        from src.auth.mailersend_manager import MailerSendManager
        
        manager = MailerSendManager(AuthenticationProvider.MAILERSEND)
        manager.set_configuration({
            'mailersend_api_token': '',
            'sender_email': 'test@example.com',
            'sender_name': 'Test Sender'
        })
        
        # Should fail validation due to empty API key
        assert manager.validate_configuration() is False

    def test_validate_configuration_success(self, mailersend_manager):
        """Test successful configuration validation."""
        result = mailersend_manager.validate_configuration()
        
        assert result is True

    def test_validate_configuration_missing_sender_email(self, mock_settings):
        """Test configuration validation fails with missing sender email."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings.sender_email = None
        manager = MailerSendManager(mock_settings)
        
        result = manager.validate_configuration()
        assert result is False

    def test_validate_configuration_invalid_sender_email(self, mock_settings):
        """Test configuration validation fails with invalid sender email."""
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings.sender_email = "invalid-email"
        manager = MailerSendManager(mock_settings)
        
        result = manager.validate_configuration()
        assert result is False

    def test_authenticate_success(self, mailersend_manager):
        """Test successful authentication with MailerSend API."""
        # Mock the client's tokens.list_tokens method directly
        with patch.object(mailersend_manager._client.tokens, 'list_tokens') as mock_list_tokens:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_list_tokens.return_value = mock_response
            
            result = mailersend_manager.authenticate()
            
            assert result is True
            assert mailersend_manager.is_authenticated is True
            assert mailersend_manager.last_authenticated is not None

    def test_authenticate_invalid_api_key(self, mailersend_manager):
        """Test authentication failure with invalid API key."""
        # Mock the client's tokens.list_tokens method directly
        with patch.object(mailersend_manager._client.tokens, 'list_tokens') as mock_list_tokens:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"message": "Invalid API key"}
            mock_list_tokens.return_value = mock_response
            
            with pytest.raises(InvalidCredentialsError) as exc_info:
                mailersend_manager.authenticate()
            
            assert "Invalid MailerSend API key" in str(exc_info.value)
            assert exc_info.value.provider == AuthenticationProvider.MAILERSEND

    @patch('src.auth.mailersend_manager.MailerSendClient')
    def test_authenticate_network_error(self, mock_client_class, mailersend_manager):
        """Test authentication failure due to network error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock network exception
        mock_client.tokens.list_tokens.side_effect = Exception("Network timeout")
        
        with pytest.raises(NetworkError) as exc_info:
            mailersend_manager.authenticate()
        
        assert "Network error during MailerSend authentication" in str(exc_info.value)
        assert exc_info.value.provider == AuthenticationProvider.MAILERSEND

    def test_send_email_success(self, mailersend_manager):
        """Test successful email sending via MailerSend."""
        # Mock authentication
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
            mock_send.assert_called_once()

    def test_send_email_not_authenticated(self, mailersend_manager):
        """Test email sending fails when not authenticated."""
        mailersend_manager.is_authenticated = False
        
        with pytest.raises(AuthenticationError) as exc_info:
            mailersend_manager.send_email(
                to_email="recipient@example.com",
                to_name="Recipient Name",
                subject="Test Subject",
                html_content="<h1>Test HTML</h1>",
                text_content="Test Text"
            )
        
        assert "Not authenticated with MailerSend" in str(exc_info.value)

    def test_send_email_missing_required_params(self, mailersend_manager):
        """Test email sending fails with missing required parameters."""
        mailersend_manager.is_authenticated = True
        
        with pytest.raises(ValueError) as exc_info:
            mailersend_manager.send_email(
                to_email="",  # Empty email
                to_name="Recipient Name",
                subject="Test Subject",
                html_content="<h1>Test HTML</h1>"
            )
        
        assert "Recipient email is required" in str(exc_info.value)

    def test_send_via_mailersend_success(self, mailersend_manager):
        """Test internal _send_via_mailersend method success."""
        mailersend_manager.is_authenticated = True
        
        # Mock EmailBuilder
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
            
            # Mock client send response
            with patch.object(mailersend_manager._client.emails, 'send') as mock_send:
                mock_response = Mock()
                mock_response.status_code = 202  # MailerSend returns 202 for accepted
                mock_send.return_value = mock_response
                
                result = mailersend_manager._send_via_mailersend(
                    to_email="recipient@example.com",
                    to_name="Recipient Name",
                    subject="Test Subject",
                    html_content="<h1>Test HTML</h1>",
                    text_content="Test Text"
                )
                
                assert result is True

    def test_html_to_text_conversion(self, mailersend_manager):
        """Test HTML to text conversion utility."""
        html_content = "<h1>Hello World</h1><p>This is a <strong>test</strong> email.</p>"
        
        text_content = mailersend_manager._html_to_text(html_content)
        
        assert "Hello World" in text_content
        assert "This is a test email." in text_content
        assert "<h1>" not in text_content
        assert "<p>" not in text_content

    def test_html_to_text_empty_content(self, mailersend_manager):
        """Test HTML to text conversion with empty content."""
        result = mailersend_manager._html_to_text("")
        assert result == ""
        
        result = mailersend_manager._html_to_text(None)
        assert result == ""

    def test_get_provider_name(self, mailersend_manager):
        """Test provider name getter."""
        assert mailersend_manager.get_provider_name() == "MailerSend"

    def test_get_authentication_status(self, mailersend_manager):
        """Test authentication status reporting."""
        # Initially not authenticated
        status = mailersend_manager.get_authentication_status()
        assert status["authenticated"] is False
        assert status["provider"] == "MailerSend"
        assert status["last_authenticated"] is None
        
        # After authentication
        mailersend_manager.is_authenticated = True
        mailersend_manager.last_authenticated = datetime.now()
        
        status = mailersend_manager.get_authentication_status()
        assert status["authenticated"] is True
        assert status["last_authenticated"] is not None

    def test_error_handling_with_detailed_messages(self, mailersend_manager):
        """Test error handling includes detailed error messages."""
        mailersend_manager.is_authenticated = True
        
        with patch.object(mailersend_manager, '_client') as mock_client:
            # Mock API error response
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.json.return_value = {
                "message": "Validation failed",
                "errors": {"email": ["Invalid email format"]}
            }
            mock_client.emails.send.return_value = mock_response
            
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


class TestMailerSendManagerIntegration:
    """Integration tests for MailerSendManager with other components."""

    def test_integration_with_authentication_factory(self):
        """Test MailerSendManager integration with AuthenticationFactory."""
        from src.auth.authentication_factory import AuthenticationFactory
        from src.auth.mailersend_manager import MailerSendManager
        
        factory = AuthenticationFactory()
        
        # This should work after we update the factory
        factory.register_provider(AuthenticationProvider.MAILERSEND, MailerSendManager)
        
        mock_settings = Mock()
        mock_settings.mailersend_api_token = "test_key"
        mock_settings.sender_email = "test@example.com"
        
        # Fix: Pass settings as config parameter, not as second argument
        config = {
            'mailersend_api_token': 'test_key',
            'sender_email': 'test@example.com'
        }
        
        manager = factory.create_manager(AuthenticationProvider.MAILERSEND, config)
        
        assert isinstance(manager, MailerSendManager)
        assert manager.provider == AuthenticationProvider.MAILERSEND

    def test_performance_requirements(self):
        """Test that MailerSend operations meet performance requirements."""
        import time
        from src.auth.mailersend_manager import MailerSendManager
        
        mock_settings = Mock()
        mock_settings.mailersend_api_token = "test_key"
        mock_settings.sender_email = "test@example.com"
        
        mailersend_manager = MailerSendManager(mock_settings)
        
        # Authentication should complete within 5 seconds
        start_time = time.time()
        
        with patch.object(mailersend_manager, '_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.tokens.list_tokens.return_value = mock_response
            
            mailersend_manager.authenticate()
        
        auth_time = time.time() - start_time
        assert auth_time < 5.0, f"Authentication took {auth_time:.2f}s, should be < 5s"
        
        # Email sending should complete within 2 seconds
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


# Mark tests for pytest
pytest.mark.mailersend = pytest.mark.mailersend
pytest.mark.unit = pytest.mark.unit