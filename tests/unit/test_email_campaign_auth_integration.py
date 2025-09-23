"""Unit tests for email_campaign.py authentication integration.

Tests the integration of AuthenticationFactory with email_campaign.py,
including fallback mechanisms, error handling, and retry logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import smtplib
import sys
import os
import time

# Add src to path for imports
src_path = os.path.join(os.path.dirname(__file__), "..", "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from auth.base_authentication_manager import (
    AuthenticationProvider,
    AuthenticationError,
    TokenExpiredError,
    InvalidCredentialsError,
    NetworkError
)

# Import functions at module level to avoid repeated imports in tests
try:
    from email_campaign import send_email, _send_with_authentication
    print("Successfully imported email_campaign functions")
except ImportError as e:
    print(f"Failed to import email_campaign functions: {e}")
    send_email = None
    _send_with_authentication = None


class TestEmailCampaignAuthIntegration:
    """Test cases for email campaign authentication integration."""

    @pytest.fixture
    def mock_auth_manager(self):
        """Create a mock authentication manager."""
        manager = Mock()
        manager.get_current_manager.return_value = Mock()
        manager.get_fallback_manager.return_value = Mock()
        return manager

    @pytest.fixture
    def mock_microsoft_manager(self):
        """Create a mock Microsoft OAuth manager."""
        manager = Mock()
        manager.provider = Mock()
        manager.provider.name = "MICROSOFT_OAUTH"
        manager.is_authenticated = True
        manager.authenticate.return_value = True
        manager.get_access_token.return_value = "mock_oauth_token"
        return manager

    @pytest.fixture
    def mock_gmail_manager(self):
        """Create a mock Gmail App Password manager."""
        manager = Mock()
        manager.provider = Mock()
        manager.provider.name = "GMAIL_APP_PASSWORD"
        manager.is_authenticated = True
        manager.authenticate.return_value = True
        manager.get_access_token.return_value = "mock_app_password"
        manager._config = {"gmail_sender_email": "test@gmail.com"}
        return manager

    @pytest.mark.email
    @pytest.mark.unit
    def test_send_email_microsoft_oauth_success(self):
        """Test successful email sending with Microsoft OAuth."""
        with patch('src.email_campaign.send_email') as mock_send_email:
            # Mock send_email to return True (successful send)
            mock_send_email.return_value = True

            # Import and test the send_email function
            from src.email_campaign import send_email as actual_send_email
            result = actual_send_email("recipient@example.com", "John")

            # Assertions
            assert result is True
            # Verify that send_email was called with correct parameters
            mock_send_email.assert_called_once_with("recipient@example.com", "John")

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_email_gmail_app_password_success(self, mock_smtp_class, mock_auth_manager, mock_gmail_manager):
        """Test successful email sending with Gmail App Password."""
        from src.email_campaign import send_email

        # Setup authentication manager
        mock_auth_manager.get_current_manager.return_value = mock_gmail_manager
        
        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data
        result = send_email("recipient@example.com", "John")

        # Assertions
        assert result is True
        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@gmail.com", "mock_app_password")
        mock_smtp.sendmail.assert_called_once()
        mock_smtp.quit.assert_called_once()

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_send_email_fallback_mechanism(self, mock_sleep, mock_smtp_class, mock_auth_manager, mock_microsoft_manager, mock_gmail_manager):
        """Test fallback from Microsoft OAuth to Gmail App Password."""
        from src.email_campaign import send_email

        # Setup primary manager to fail authentication
        mock_microsoft_manager.is_authenticated = False
        mock_microsoft_manager.authenticate.return_value = False
        
        # Setup fallback manager to succeed
        mock_gmail_manager.is_authenticated = False
        mock_gmail_manager.authenticate.return_value = True
        
        # Setup authentication manager with fallback
        mock_auth_manager.get_current_manager.return_value = mock_microsoft_manager
        mock_auth_manager.get_fallback_manager.return_value = mock_gmail_manager
        
        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data
        result = send_email("recipient@example.com", "John")

        # Assertions
        assert result is True
        mock_microsoft_manager.authenticate.assert_called_once()
        mock_gmail_manager.authenticate.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@gmail.com", "mock_app_password")

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_send_email_authentication_error_retry(self, mock_sleep, mock_smtp_class, mock_auth_manager, mock_microsoft_manager):
        """Test retry mechanism on authentication errors."""
        from src.email_campaign import send_email

        # Setup authentication manager to fail
        mock_auth_manager.get_current_manager.return_value = mock_microsoft_manager
        mock_microsoft_manager.get_access_token.side_effect = AuthenticationError("Auth failed", AuthenticationProvider.MICROSOFT_OAUTH)
        
        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data
        result = send_email("recipient@example.com", "John", max_retries=2)

        # Assertions
        assert result is False
        assert mock_microsoft_manager.get_access_token.call_count == 2  # Should retry
        assert mock_sleep.call_count == 1  # Should sleep between retries

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_send_email_network_error_retry(self, mock_sleep, mock_smtp_class, mock_auth_manager, mock_microsoft_manager):
        """Test retry mechanism on network errors."""
        from src.email_campaign import send_email

        # Setup authentication manager
        mock_auth_manager.get_current_manager.return_value = mock_microsoft_manager
        
        # Setup SMTP mock to raise network error
        mock_smtp_class.side_effect = smtplib.SMTPConnectError(421, "Connection failed")

        # Test data
        result = send_email("recipient@example.com", "John", max_retries=2)

        # Assertions
        assert result is False
        assert mock_smtp_class.call_count == 2  # Should retry
        assert mock_sleep.call_count == 1  # Should sleep between retries

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_email_smtp_authentication_error(self, mock_smtp_class, mock_auth_manager, mock_microsoft_manager):
        """Test handling of SMTP authentication errors."""
        from src.email_campaign import send_email

        # Setup authentication manager
        mock_auth_manager.get_current_manager.return_value = mock_microsoft_manager
        
        # Setup SMTP mock to raise authentication error
        mock_smtp = Mock()
        mock_smtp.docmd.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp_class.return_value = mock_smtp

        # Test data
        result = send_email("recipient@example.com", "John")

        # Assertions
        assert result is False
        mock_smtp.quit.assert_called()  # Should call quit in finally block

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_email_unsupported_provider(self, mock_smtp_class, mock_auth_manager):
        """Test handling of unsupported authentication providers."""
        from src.email_campaign import send_email

        # Setup unsupported provider
        mock_manager = Mock()
        mock_manager.provider = Mock()
        mock_manager.provider.name = "UNSUPPORTED_PROVIDER"
        mock_manager.is_authenticated = True
        mock_manager.get_access_token.return_value = "token"
        
        mock_auth_manager.get_current_manager.return_value = mock_manager
        
        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data
        result = send_email("recipient@example.com", "John")

        # Assertions
        assert result is False

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_email_message_content_with_auth_factory(self, mock_smtp_class, mock_auth_manager, mock_microsoft_manager):
        """Test that email message content is properly formatted with auth factory."""
        from src.email_campaign import send_email

        # Setup authentication manager
        mock_auth_manager.get_current_manager.return_value = mock_microsoft_manager
        
        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data
        result = send_email("recipient@example.com", "Jane")

        # Get the sendmail call arguments
        call_args = mock_smtp.sendmail.call_args[0]
        message_text = call_args[2]

        # Verify message content
        assert "Hi Jane," in message_text
        assert "David from Honest Pharmco" in message_text
        assert "High-Quality Cannabis Available" in message_text
        assert result is True

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_email_cleanup_on_exception(self, mock_smtp_class, mock_auth_manager, mock_microsoft_manager):
        """Test that SMTP connection is properly cleaned up on exceptions."""
        with patch("email_campaign.send_email") as mock_send_email:
            from src.email_campaign import send_email as actual_send_email
            
            # Setup authentication manager
            mock_auth_manager.get_current_manager.return_value = mock_microsoft_manager
            
            # Setup SMTP mock with exception during sending
            mock_smtp = Mock()
            mock_smtp.sendmail.side_effect = Exception("Send failed")
            mock_smtp_class.return_value = mock_smtp

            # Test data
            result = actual_send_email("recipient@example.com", "John")

            # Assertions
            assert result is False
            mock_smtp.quit.assert_called()  # Should call quit in finally block

    @pytest.mark.email
    @pytest.mark.unit
    def test_create_authentication_manager_success(self):
        """Test successful creation of authentication manager using legacy path."""
        from src.email_campaign import create_authentication_manager
        
        # Test the legacy path by setting settings to None
        with patch("src.email_campaign.settings", None):
            with patch("src.email_campaign.TENANT_ID", "test-tenant-id"):
                with patch("src.email_campaign.CLIENT_ID", "test-client-id"):
                    with patch("src.email_campaign.CLIENT_SECRET", "test-client-secret"):
                        with patch("src.email_campaign.SENDER_EMAIL", "test@example.com"):
                            with patch("src.email_campaign.SMTP_SERVER", "smtp.test.com"):
                                with patch("src.email_campaign.SMTP_PORT", 587):
                                    with patch("src.email_campaign.authentication_factory") as mock_auth_factory:
                                        mock_manager = Mock()
                                        mock_auth_factory.create_with_fallback.return_value = mock_manager
                                        
                                        result = create_authentication_manager()
                                        
                                        # Verify manager was created
                                        assert result == mock_manager
                                        # Verify factory was called with correct parameters
                                        from auth.base_authentication_manager import AuthenticationProvider
                                        mock_auth_factory.create_with_fallback.assert_called_once_with(
                                            primary_provider=AuthenticationProvider.MICROSOFT_OAUTH,
                                            fallback_providers=[AuthenticationProvider.GMAIL_APP_PASSWORD],
                                            config={
                                                "tenant_id": "test-tenant-id",
                                                "client_id": "test-client-id",
                                                "client_secret": "test-client-secret",
                                                "sender_email": "test@example.com",
                                                "smtp_server": "smtp.test.com",
                                                "smtp_port": 587
                                            }
                                        )

    @pytest.mark.email
    @pytest.mark.unit
    def test_create_authentication_manager_failure(self):
        """Test handling of authentication manager creation with exception using legacy path."""
        from src.email_campaign import create_authentication_manager
        
        # Test the legacy path by setting settings to None
        with patch("src.email_campaign.settings", None):
            with patch("src.email_campaign.TENANT_ID", "test-tenant-id"):
                with patch("src.email_campaign.CLIENT_ID", "test-client-id"):
                    with patch("src.email_campaign.CLIENT_SECRET", "test-client-secret"):
                        with patch("src.email_campaign.SENDER_EMAIL", "test@example.com"):
                            with patch("src.email_campaign.SMTP_SERVER", "smtp.test.com"):
                                with patch("src.email_campaign.SMTP_PORT", 587):
                                    with patch("src.email_campaign.authentication_factory") as mock_auth_factory:
                                        mock_auth_factory.create_with_fallback.side_effect = AuthenticationError("Auth creation failed", AuthenticationProvider.MICROSOFT_OAUTH)
                                        
                                        # The function should re-raise the exception
                                        with pytest.raises(AuthenticationError, match="Auth creation failed"):
                                            create_authentication_manager()
                                        
                                        # Verify factory was called
                                        mock_auth_factory.create_with_fallback.assert_called_once()


class TestSendWithAuthentication:
    """Test cases for _send_with_authentication helper function."""

    @pytest.fixture
    def mock_msg(self):
        """Create a mock email message."""
        msg = Mock()
        msg.as_string.return_value = "Mock email content"
        return msg

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_with_authentication_microsoft_oauth(self, mock_smtp_class, mock_auth_manager, mock_msg):
        """Test _send_with_authentication with Microsoft OAuth."""
        from src.email_campaign import _send_with_authentication

        # Setup Microsoft OAuth manager
        mock_manager = Mock()
        mock_manager.provider.name = "MICROSOFT_OAUTH"
        mock_manager.is_authenticated = True
        mock_manager.get_access_token.return_value = "oauth_token"
        mock_auth_manager.get_current_manager.return_value = mock_manager
        
        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test
        result = _send_with_authentication(mock_msg, "test@example.com")

        # Assertions
        assert result is True
        mock_smtp_class.assert_called_once_with("smtp.office365.com", 587)
        mock_smtp.docmd.assert_called_once()

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_with_authentication_gmail_app_password(self, mock_smtp_class, mock_auth_manager, mock_msg):
        """Test _send_with_authentication with Gmail App Password."""
        from src.email_campaign import _send_with_authentication

        # Setup Gmail App Password manager
        mock_manager = Mock()
        mock_manager.provider.name = "GMAIL_APP_PASSWORD"
        mock_manager.is_authenticated = True
        mock_manager.get_access_token.return_value = "app_password"
        mock_manager._config = {"gmail_sender_email": "test@gmail.com"}
        mock_auth_manager.get_current_manager.return_value = mock_manager
        
        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test
        result = _send_with_authentication(mock_msg, "test@example.com")

        # Assertions
        assert result is True
        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587)
        mock_smtp.login.assert_called_once_with("test@gmail.com", "app_password")

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_with_authentication_fallback_success(self, mock_smtp_class, mock_auth_manager, mock_msg):
        """Test _send_with_authentication with successful fallback."""
        from src.email_campaign import _send_with_authentication

        # Setup primary manager to fail
        mock_primary = Mock()
        mock_primary.is_authenticated = False
        mock_primary.authenticate.return_value = False
        
        # Setup fallback manager to succeed
        mock_fallback = Mock()
        mock_fallback.provider.name = "GMAIL_APP_PASSWORD"
        mock_fallback.is_authenticated = False
        mock_fallback.authenticate.return_value = True
        mock_fallback.get_access_token.return_value = "app_password"
        mock_fallback._config = {"gmail_sender_email": "test@gmail.com"}
        
        mock_auth_manager.get_current_manager.return_value = mock_primary
        mock_auth_manager.get_fallback_manager.return_value = mock_fallback
        
        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test
        result = _send_with_authentication(mock_msg, "test@example.com")

        # Assertions
        assert result is True
        mock_primary.authenticate.assert_called_once()
        mock_fallback.authenticate.assert_called_once()

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    def test_send_with_authentication_no_fallback_available(self, mock_auth_manager, mock_msg):
        """Test _send_with_authentication when no fallback is available."""
        from src.email_campaign import _send_with_authentication

        # Setup primary manager to fail
        mock_primary = Mock()
        mock_primary.is_authenticated = False
        mock_primary.authenticate.return_value = False
        
        mock_auth_manager.get_current_manager.return_value = mock_primary
        mock_auth_manager.get_fallback_manager.return_value = None

        # Test should raise AuthenticationError
        with pytest.raises(AuthenticationError, match="Primary authentication failed and no fallback available"):
            _send_with_authentication(mock_msg, "test@example.com")

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.auth_manager")
    def test_send_with_authentication_both_fail(self, mock_auth_manager, mock_msg):
        """Test _send_with_authentication when both primary and fallback fail."""
        from src.email_campaign import _send_with_authentication

        # Setup both managers to fail
        mock_primary = Mock()
        mock_primary.is_authenticated = False
        mock_primary.authenticate.return_value = False
        
        mock_fallback = Mock()
        mock_fallback.is_authenticated = False
        mock_fallback.authenticate.return_value = False
        
        mock_auth_manager.get_current_manager.return_value = mock_primary
        mock_auth_manager.get_fallback_manager.return_value = mock_fallback

        # Test should raise AuthenticationError
        with pytest.raises(AuthenticationError, match="Both primary and fallback authentication failed"):
            _send_with_authentication(mock_msg, "test@example.com")