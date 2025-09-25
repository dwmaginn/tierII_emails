"""Unit tests for email-related functions.

Tests get_first_name(), send_email(), and MailerSend integration functions.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import the functions we need to test
try:
    from email_campaign import get_first_name, send_email
    import email_campaign
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
            ("", "Friend"),  # Updated to use settings fallback
            (" ", "Friend"),  # Updated to use settings fallback
            ("SingleName", "SingleName"),
            ("  John  Doe  ", "John"),  # Test whitespace handling
            ("Dr.", "Friend"),  # Only title, updated to use settings fallback
            ("123 Main St", "123"),  # Non-name input
            ("Jean-Pierre Dupont", "Jean-Pierre"),  # Hyphenated names
            ("O'Connor", "O'Connor"),  # Apostrophe names
            ("Mr. John", "John"),  # Title with single name
            ("Mrs. Jane", "Jane"),  # Title with single name
            ("Dr. Bob", "Bob"),  # Title with single name
            ("Rev. Michael", "Michael"),  # Religious title
            ("Prof. Lisa", "Lisa"),  # Academic title
            ("Sir David", "David"),  # Honorific title
            ("Madam President", "President"),  # Formal title
            ("mr john doe", "john"),  # Lowercase title
            ("DR. JANE SMITH", "JANE"),  # Uppercase title
            ("Ms.", "Friend"),  # Only title with period, updated to use settings fallback
            ("Rev.", "Friend"),  # Only religious title, updated to use settings fallback
        ],
    )
    def test_get_first_name_extraction(self, input_name, expected_first_name):
        """Test first name extraction from various contact name formats."""
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_fallback_first_name = "Friend"
            result = get_first_name(input_name)
            assert result == expected_first_name

    @pytest.mark.email
    @pytest.mark.unit
    def test_get_first_name_with_none_input(self):
        """Test get_first_name with None input."""
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_fallback_first_name = "Friend"
            result = get_first_name(None)
            assert result == "Friend"

    @pytest.mark.email
    @pytest.mark.unit
    def test_get_first_name_with_custom_fallback(self):
        """Test get_first_name with custom fallback name."""
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_fallback_first_name = "Valued Customer"
            result = get_first_name("")
            assert result == "Valued Customer"

    @pytest.mark.email
    @pytest.mark.unit
    def test_get_first_name_title_variations(self):
        """Test get_first_name with various title formats."""
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_fallback_first_name = "Friend"
            
            # Test titles with and without periods
            assert get_first_name("Mr John Smith") == "John"
            assert get_first_name("Mr. John Smith") == "John"
            assert get_first_name("DR Jane Doe") == "Jane"
            assert get_first_name("Dr. Jane Doe") == "Jane"
            assert get_first_name("prof alice johnson") == "alice"
            assert get_first_name("Prof. Alice Johnson") == "Alice"

    @pytest.mark.email
    @pytest.mark.unit
    def test_send_email_mailersend_success(self):
        """Test successful email sending via MailerSend."""
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@example.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("recipient@example.com", "John")
            
            assert result is True
            mock_manager.send_email.assert_called_once()
            call_args = mock_manager.send_email.call_args
            assert call_args[1]['to_email'] == "recipient@example.com"
            assert 'html_content' in call_args[1]
            assert "Hi John," in call_args[1]['html_content']

    @pytest.mark.email
    @pytest.mark.unit
    def test_send_email_mailersend_failure(self):
        """Test email sending failure via MailerSend."""
        mock_manager = Mock()
        mock_manager.send_email.return_value = False
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@example.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("recipient@example.com", "John")
            
            assert result is False

    @pytest.mark.email
    @pytest.mark.unit
    def test_send_email_no_auth_manager(self):
        """Test email sending when auth manager is None."""
        mock_settings = Mock()
        mock_settings.sender_email = "test@example.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', None), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("recipient@example.com", "John")
            
            assert result is False

    @pytest.mark.email
    @pytest.mark.unit
    def test_send_email_with_retry_logic(self):
        """Test email sending with retry logic."""
        from auth.base_authentication_manager import AuthenticationError, AuthenticationProvider
        
        mock_manager = Mock()
        # First call fails, second succeeds
        mock_manager.send_email.side_effect = [
            AuthenticationError("Auth failed", AuthenticationProvider.MAILERSEND),
            True
        ]
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@example.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            result = send_email("recipient@example.com", "John", max_retries=2)
            
            assert result is True
            assert mock_manager.send_email.call_count == 2

    @pytest.mark.email
    @pytest.mark.unit
    def test_send_email_max_retries_exceeded(self):
        """Test email sending when max retries are exceeded."""
        from auth.base_authentication_manager import AuthenticationError, AuthenticationProvider
        
        mock_manager = Mock()
        mock_manager.send_email.side_effect = AuthenticationError("Auth failed", AuthenticationProvider.MAILERSEND)
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@example.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            result = send_email("recipient@example.com", "John", max_retries=2)
            
            assert result is False
            assert mock_manager.send_email.call_count == 2

    @pytest.mark.email
    @pytest.mark.unit
    def test_send_email_content_personalization(self):
        """Test email content personalization."""
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@example.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings):
            
            # Test with different first names
            send_email("recipient@example.com", "Alice")
            call_args = mock_manager.send_email.call_args
            assert "Hi Alice," in call_args[1]['html_content']
            
            mock_manager.reset_mock()
            
            send_email("recipient@example.com", "Bob")
            call_args = mock_manager.send_email.call_args
            assert "Hi Bob," in call_args[1]['html_content']

    @pytest.mark.email
    @pytest.mark.unit
    def test_send_email_subject_line(self):
        """Test email subject line is correctly set."""
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@example.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings):
            
            send_email("recipient@example.com", "John")
            
            call_args = mock_manager.send_email.call_args
            assert call_args[1]['subject'] == "High-Quality Cannabis Available - Honest Pharmco"

    @pytest.mark.email
    @pytest.mark.unit
    def test_send_email_body_content(self):
        """Test email body contains expected content."""
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@example.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings):
            
            send_email("recipient@example.com", "John")
            
            call_args = mock_manager.send_email.call_args
            body = call_args[1]['html_content']
            
            # Check for key content elements
            assert "Hi John," in body
            assert "Honest Pharmco" in body
            assert "high-quality cannabis products" in body
            assert "Premium Quality" in body
            assert "Diverse Selection" in body
            assert "Competitive Pricing" in body
            assert "Discreet Delivery" in body
            assert "Expert Support" in body
            assert "David Maginn" in body
            assert "contact@honestpharmco.com" in body
            assert "15% discount" in body
            assert "UNSUBSCRIBE" in body


class TestEmailCampaignIntegration:
    """Integration tests for email campaign functionality."""

    @pytest.mark.email
    @pytest.mark.unit
    def test_read_contacts_from_csv(self):
        """Test reading contacts from CSV file."""
        from email_campaign import read_contacts_from_csv
        
        # Mock CSV content
        csv_content = [
            {"Primary Contact Name": "John Doe", "Email": "john@example.com"},
            {"Primary Contact Name": "Jane Smith", "Email": "jane@example.com"},
            {"Primary Contact Name": "Invalid Entry", "Email": ""},  # Should be filtered out
            {"Primary Contact Name": "Bob Wilson", "Email": "bob@example.com"},
        ]
        
        with patch('builtins.open', create=True) as mock_open, \
             patch('csv.DictReader') as mock_csv_reader:
            
            mock_csv_reader.return_value = csv_content
            
            contacts = read_contacts_from_csv("test.csv")
            
            # Should have 3 valid contacts (invalid email filtered out)
            assert len(contacts) == 3
            assert contacts[0]["email"] == "john@example.com"
            assert contacts[0]["first_name"] == "John"
            assert contacts[1]["email"] == "jane@example.com"
            assert contacts[1]["first_name"] == "Jane"
            assert contacts[2]["email"] == "bob@example.com"
            assert contacts[2]["first_name"] == "Bob"

    @pytest.mark.email
    @pytest.mark.unit
    def test_send_batch_emails(self):
        """Test sending batch of emails."""
        from email_campaign import send_batch_emails
        
        contacts = [
            {"email": "test1@example.com", "first_name": "John"},
            {"email": "test2@example.com", "first_name": "Jane"},
            {"email": "test3@example.com", "first_name": "Bob"},
        ]
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            mock_send_email.return_value = True
            
            successful_sends, next_index = send_batch_emails(contacts, 0, 2)
            
            assert successful_sends == 2
            assert next_index == 2
            assert mock_send_email.call_count == 2
            mock_send_email.assert_any_call("test1@example.com", "John")
            mock_send_email.assert_any_call("test2@example.com", "Jane")