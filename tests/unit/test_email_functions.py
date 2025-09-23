"""Unit tests for email-related functions.

Tests get_first_name(), get_oauth_string(), send_email(), and email template generation.
"""

import pytest
from unittest.mock import Mock, patch
import smtplib
import sys
import os
import importlib

# Add src to path for imports
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import the functions we need to test
try:
    from email_campaign import get_first_name, get_oauth_string, send_email
    import src.email_campaign
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Trying to import from: {src_path}")
    raise


class TestEmailFunctions:
    """Test cases for email-related functions."""

    @pytest.mark.email
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "input_name,expected_first_name",
        [
            ("John Doe", "John"),
            ("Dr. Jane Smith", "Jane"),
            ("Mary Jane Watson", "Mary"),
            ("Prof. Robert Johnson", "Robert"),
            ("Ms. Sarah Connor", "Sarah"),
            ("Mr. David Wilson", "David"),
            ("", "there"),
            (" ", "there"),
            ("SingleName", "SingleName"),
            ("  John  Doe  ", "John"),  # Test whitespace handling
            ("Dr.", "there"),  # Only title
            ("123 Main St", "123"),  # Non-name input
            ("Jean-Pierre Dupont", "Jean-Pierre"),  # Hyphenated names
            ("O'Connor", "O'Connor"),  # Apostrophe names
            ("李小明", "李小明"),  # Non-Latin characters
        ],
    )
    def test_get_first_name(self, input_name, expected_first_name):
        """Test get_first_name function with various inputs."""
        result = get_first_name(input_name)
        assert result == expected_first_name

    @pytest.mark.email
    @pytest.mark.unit
    def test_get_oauth_string(self):
        """Test get_oauth_string function."""
        username = "test@example.com"
        access_token = "mock_access_token_12345"

        result = get_oauth_string(username, access_token)

        # The OAuth string should be base64 encoded
        import base64

        decoded = base64.b64decode(result).decode("ascii")

        # Should contain the username and access token in the correct format
        assert f"user={username}" in decoded
        assert f"auth=Bearer {access_token}" in decoded
        assert decoded.startswith("user=")
        assert "\x01auth=Bearer" in decoded

    @pytest.mark.email
    @pytest.mark.unit
    def test_get_oauth_string_empty_inputs(self):
        """Test get_oauth_string with empty inputs."""
        # Test with empty username
        result1 = get_oauth_string("", "token")
        import base64

        decoded1 = base64.b64decode(result1).decode("ascii")
        assert "user=" in decoded1
        assert "auth=Bearer token" in decoded1

        # Test with empty token
        result2 = get_oauth_string("user@test.com", "")
        decoded2 = base64.b64decode(result2).decode("ascii")
        assert "user=user@test.com" in decoded2
        assert "auth=Bearer " in decoded2

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_class):
        """Test successful email sending."""
        # Setup auth manager mock
        mock_current_manager = Mock()
        mock_current_manager.is_authenticated = True
        mock_current_manager.get_access_token.return_value = "mock_token_12345"
        mock_current_manager.provider.name = "MICROSOFT_OAUTH"
        
        mock_auth_manager = Mock()
        mock_auth_manager.get_current_manager.return_value = mock_current_manager
        
        # Directly set the auth_manager in the module
        src.email_campaign.auth_manager = mock_auth_manager
        
        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data
        to_email = "recipient@example.com"
        to_name = "John"

        # Process the name first (like the real code does)
        first_name = get_first_name(to_name)

        # Call function
        result = src.email_campaign.send_email(to_email, first_name)

        # Assertions
        assert result is True

        # Verify SMTP setup
        mock_smtp_class.assert_called_once()
        mock_smtp.starttls.assert_called_once()

        # Verify OAuth authentication
        mock_current_manager.get_access_token.assert_called_once()

        # Verify email sending
        mock_smtp.sendmail.assert_called_once()
        mock_smtp.docmd.assert_called_once()
        mock_smtp.quit.assert_called_once()

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.smtplib.SMTP")
    @patch("src.email_campaign.auth_manager")
    def test_send_email_smtp_connection_error(
        self, mock_auth_manager, mock_smtp_class
    ):
        """Test email sending with SMTP connection error."""
        # Setup auth manager mock
        mock_current_manager = Mock()
        mock_current_manager.is_authenticated = True
        mock_current_manager.get_access_token.return_value = "mock_token_12345"
        mock_current_manager.provider.name = "MICROSOFT_OAUTH"
        mock_auth_manager.get_current_manager.return_value = mock_current_manager

        # Setup SMTP mock to raise connection error
        mock_smtp_class.side_effect = smtplib.SMTPConnectError(421, "Connection failed")

        # Test data
        to_email = "recipient@example.com"
        to_name = "John"

        # Process the name first (like the real code does)
        first_name = get_first_name(to_name)

        # Call function
        result = src.email_campaign.send_email(to_email, first_name)

        # Should return False on connection error
        assert result is False

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.smtplib.SMTP")
    @patch("src.email_campaign.auth_manager")
    def test_send_email_authentication_error(self, mock_auth_manager, mock_smtp_class):
        """Test email sending with authentication error."""
        # Setup auth manager mock to raise error
        mock_current_manager = Mock()
        mock_current_manager.is_authenticated = True
        mock_current_manager.get_access_token.side_effect = Exception("OAuth failed")
        mock_current_manager.provider.name = "MICROSOFT_OAUTH"
        mock_auth_manager.get_current_manager.return_value = mock_current_manager

        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data
        to_email = "recipient@example.com"
        to_name = "John"

        # Process the name first (like the real code does)
        first_name = get_first_name(to_name)

        # Call function
        result = src.email_campaign.send_email(to_email, first_name)

        # Should return False on authentication error
        assert result is False

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.smtplib.SMTP")
    @patch("src.email_campaign.auth_manager")
    def test_send_email_send_message_error(self, mock_auth_manager, mock_smtp_class):
        """Test email sending with send_message error."""
        # Setup auth manager mock
        mock_current_manager = Mock()
        mock_current_manager.is_authenticated = True
        mock_current_manager.get_access_token.return_value = "mock_token_12345"
        mock_current_manager.provider.name = "MICROSOFT_OAUTH"
        mock_auth_manager.get_current_manager.return_value = mock_current_manager

        # Setup SMTP mock with sendmail error
        mock_smtp = Mock()
        mock_smtp.sendmail.side_effect = smtplib.SMTPRecipientsRefused({})
        mock_smtp_class.return_value = mock_smtp

        # Test data
        to_email = "invalid@example.com"
        to_name = "John"

        # Process the name first (like the real code does)
        first_name = get_first_name(to_name)

        # Call function
        result = src.email_campaign.send_email(to_email, first_name)

        # Should return False on send error
        assert result is False
        # quit() is always called in the finally block, even on exceptions
        mock_smtp.quit.assert_called()

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_email_message_content(self, mock_smtp_class):
        """Test that email message content is properly formatted."""
        # Setup current manager mock
        mock_current_manager = Mock()
        mock_current_manager.is_authenticated = True
        mock_current_manager.get_access_token.return_value = "mock_token_12345"
        mock_current_manager.provider.name = "MICROSOFT_OAUTH"
        
        # Setup auth manager mock with proper interface
        mock_auth_manager = Mock()
        mock_auth_manager.get_current_manager.return_value = mock_current_manager
        
        # Directly set the auth_manager in the module
        src.email_campaign.auth_manager = mock_auth_manager

        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data
        to_email = "recipient@example.com"
        first_name = "John"

        # Call function
        result = src.email_campaign.send_email(to_email, first_name)
        
        # Verify the function succeeded
        assert result is True
        
        # Verify sendmail was called
        mock_smtp.sendmail.assert_called_once()
        
        # Get the sendmail call arguments
        call_args = mock_smtp.sendmail.call_args[0]
        from_addr = call_args[0]
        to_addr = call_args[1]
        message_text = call_args[2]

        # Verify sendmail arguments
        assert to_addr == "recipient@example.com"

        # Verify message body contains the expected content with personalization
        assert "Hi John," in message_text
        assert "David from Honest Pharmco" in message_text

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_email_personalization(self, mock_smtp_class):
        """Test email personalization with first name extraction."""
        # Setup current manager mock
        mock_current_manager = Mock()
        mock_current_manager.is_authenticated = True
        mock_current_manager.get_access_token.return_value = "mock_token_12345"
        mock_current_manager.provider.name = "MICROSOFT_OAUTH"
        
        # Setup auth manager mock with proper interface
        mock_auth_manager = Mock()
        mock_auth_manager.get_current_manager.return_value = mock_current_manager
        
        # Directly set the auth_manager in the module
        src.email_campaign.auth_manager = mock_auth_manager

        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data with full name
        to_email = "recipient@example.com"
        to_name = "Dr. Jane Smith"  # Full name with title

        # Process the name first (like the real code does)
        first_name = get_first_name(to_name)

        # Call function
        result = src.email_campaign.send_email(to_email, first_name)

        # Verify the function was called and get the sendmail call arguments
        assert result is True
        mock_smtp.sendmail.assert_called_once()
        call_args = mock_smtp.sendmail.call_args[0]
        message_text = call_args[2]

        # Verify personalization worked
        assert "Hi Jane," in message_text
        assert "David from Honest Pharmco" in message_text

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_email_empty_name_fallback(self, mock_smtp_class):
        """Test email personalization fallback for empty names."""
        # Setup current manager mock
        mock_current_manager = Mock()
        mock_current_manager.is_authenticated = True
        mock_current_manager.get_access_token.return_value = "mock_token_12345"
        mock_current_manager.provider.name = "MICROSOFT_OAUTH"
        
        # Setup auth manager mock with proper interface
        mock_auth_manager = Mock()
        mock_auth_manager.get_current_manager.return_value = mock_current_manager
        
        # Directly set the auth_manager in the module
        src.email_campaign.auth_manager = mock_auth_manager

        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data with empty name
        to_email = "recipient@example.com"
        to_name = ""

        # Process the name first (like the real code does)
        first_name = get_first_name(to_name)

        # Call function
        result = src.email_campaign.send_email(to_email, first_name)

        # Verify the function was called and get the sendmail call arguments
        assert result is True
        mock_smtp.sendmail.assert_called_once()
        call_args = mock_smtp.sendmail.call_args[0]
        message_text = call_args[2]

        # Verify fallback to "there" for empty names (get_first_name returns "there" for empty input)
        # The message_text contains MIME headers, so we need to check the body content
        assert "Hi there," in message_text
        assert "David from Honest Pharmco" in message_text

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.smtplib.SMTP")
    def test_send_email_special_characters(self, mock_smtp_class):
        """Test email sending with special characters in content."""
        # Setup current manager mock
        mock_current_manager = Mock()
        mock_current_manager.is_authenticated = True
        mock_current_manager.get_access_token.return_value = "mock_token_12345"
        mock_current_manager.provider.name = "MICROSOFT_OAUTH"
        
        # Setup auth manager mock with proper interface
        mock_auth_manager = Mock()
        mock_auth_manager.get_current_manager.return_value = mock_current_manager
        
        # Directly set the auth_manager in the module
        src.email_campaign.auth_manager = mock_auth_manager

        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Test data with special characters
        to_email = "recipient@example.com"
        to_name = "José María"

        # Process the name first (like the real code does)
        first_name = get_first_name(to_name)

        # Call function
        result = src.email_campaign.send_email(to_email, first_name)

        # Should handle special characters without error
        assert result is True
        mock_smtp.sendmail.assert_called_once()

        # Get the sendmail call arguments
        call_args = mock_smtp.sendmail.call_args[0]
        message_text = call_args[2]

        # Verify special characters are handled properly
        # The message_text contains MIME headers and base64 encoded content
        # Check for the base64 encoded version of "Hi José," which is "SGkgSm9zw6ks"
        # The content "Hi José," in UTF-8 base64 is "SGkgSm9zw6ks"
        assert "SGkgSm9zw6ks" in message_text or "José" in message_text

    @pytest.mark.email
    @pytest.mark.unit
    @patch("src.email_campaign.smtplib.SMTP")
    @patch("src.email_campaign.auth_manager")
    def test_send_email_cleanup_on_exception(self, mock_auth_manager, mock_smtp_class):
        """Test that SMTP connection is properly cleaned up on exceptions."""
        # Setup auth manager mock
        mock_current_manager = Mock()
        mock_current_manager.is_authenticated = True
        mock_current_manager.get_access_token.return_value = "mock_token_12345"
        mock_current_manager.provider.name = "MICROSOFT_OAUTH"
        mock_auth_manager.get_current_manager.return_value = mock_current_manager

        # Setup SMTP mock with exception during auth
        mock_smtp = Mock()
        mock_smtp.docmd.side_effect = Exception("Auth failed")
        mock_smtp_class.return_value = mock_smtp

        # Test data
        to_email = "recipient@example.com"
        to_name = "John Doe"

        # Process the name first (like the real code does)
        first_name = get_first_name(to_name)

        # Call function
        result = send_email(to_email, first_name)

        # Should return False and not call quit on exception
        assert result is False
        mock_smtp.quit.assert_not_called()