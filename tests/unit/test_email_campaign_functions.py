"""Unit tests for email campaign functions.

This module contains comprehensive tests for the email campaign workflow functions,
including name processing, email sending with retry logic, CSV data import, and
batch processing functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
import csv
import io
import time
from datetime import datetime

# Import the functions to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from auth.base_authentication_manager import (
    AuthenticationError,
    NetworkError,
    AuthenticationProvider
)


class TestGetFirstNameFunction:
    """Test suite for get_first_name() function."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with fallback first name."""
        settings = Mock()
        settings.test_fallback_first_name = "Friend"
        return settings

    def test_get_first_name_simple_name(self):
        """Test get_first_name with simple first and last name."""
        from email_campaign import get_first_name
        
        result = get_first_name("John Doe")
        
        assert result == "John"

    def test_get_first_name_multiple_names(self):
        """Test get_first_name with multiple name parts."""
        from email_campaign import get_first_name
        
        result = get_first_name("Mary Jane Smith")
        
        assert result == "Mary"

    def test_get_first_name_single_name(self):
        """Test get_first_name with single name only."""
        from email_campaign import get_first_name
        
        result = get_first_name("Madonna")
        
        assert result == "Madonna"

    def test_get_first_name_empty_string(self):
        """Test get_first_name with empty string input."""
        from email_campaign import get_first_name
        
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_fallback_first_name = "Friend"
            result = get_first_name("")
            
            assert result == "Friend"

    def test_get_first_name_none_input(self):
        """Test get_first_name with None input."""
        from email_campaign import get_first_name
        
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_fallback_first_name = "Friend"
            result = get_first_name(None)
            
            assert result == "Friend"

    def test_get_first_name_whitespace_only(self):
        """Test get_first_name with whitespace-only string."""
        from email_campaign import get_first_name
        
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_fallback_first_name = "Friend"
            result = get_first_name("   ")
            
            assert result == "Friend"

    def test_get_first_name_with_title_mr(self):
        """Test get_first_name removes 'Mr' title."""
        from email_campaign import get_first_name
        
        result = get_first_name("Mr John Smith")
        
        assert result == "John"

    def test_get_first_name_with_title_mrs(self):
        """Test get_first_name removes 'Mrs' title."""
        from email_campaign import get_first_name
        
        result = get_first_name("Mrs Jane Doe")
        
        assert result == "Jane"

    def test_get_first_name_with_title_dr(self):
        """Test get_first_name removes 'Dr' title."""
        from email_campaign import get_first_name
        
        result = get_first_name("Dr Michael Johnson")
        
        assert result == "Michael"

    def test_get_first_name_with_title_period(self):
        """Test get_first_name removes titles with periods."""
        from email_campaign import get_first_name
        
        result = get_first_name("Dr. Sarah Wilson")
        
        assert result == "Sarah"

    def test_get_first_name_title_only(self):
        """Test get_first_name with title only falls back to default."""
        from email_campaign import get_first_name
        
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_fallback_first_name = "Friend"
            result = get_first_name("Mr")
            
            assert result == "Friend"

    def test_get_first_name_special_characters(self):
        """Test get_first_name with special characters in names."""
        from email_campaign import get_first_name
        
        result = get_first_name("José María García")
        
        assert result == "José"

    def test_get_first_name_hyphenated_name(self):
        """Test get_first_name with hyphenated first name."""
        from email_campaign import get_first_name
        
        result = get_first_name("Mary-Jane Watson")
        
        assert result == "Mary-Jane"

    def test_get_first_name_case_insensitive_titles(self):
        """Test get_first_name handles case-insensitive title removal."""
        from email_campaign import get_first_name
        
        result = get_first_name("MR JOHN SMITH")
        
        assert result == "JOHN"


class TestSendEmailCampaignFunction:
    """Test suite for send_email() campaign function with retry logic."""

    @pytest.fixture
    def mock_auth_manager(self):
        """Mock authentication manager."""
        manager = Mock()
        manager.send_email.return_value = True
        return manager

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for email campaign."""
        settings = Mock()
        settings.sender_email = "test@honestpharmco.com"
        settings.sender_name = "Test Sender"
        return settings

    def test_send_email_success_first_attempt(self):
        """Test successful email sending on first attempt."""
        from email_campaign import send_email
        
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@honestpharmco.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("recipient@example.com", "John")
            
            assert result is True
            mock_manager.send_email.assert_called_once()
            call_args = mock_manager.send_email.call_args
            assert call_args[1]['recipient_email'] == "recipient@example.com"
            assert call_args[1]['sender_email'] == "test@honestpharmco.com"

    def test_send_email_success_after_retry(self):
        """Test successful email sending after initial failure."""
        from email_campaign import send_email
        
        mock_manager = Mock()
        # First call fails, second succeeds
        mock_manager.send_email.side_effect = [False, True]
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@honestpharmco.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            result = send_email("recipient@example.com", "John", max_retries=3)
            
            assert result is True
            assert mock_manager.send_email.call_count == 2

    def test_send_email_all_retries_fail(self):
        """Test email sending fails after all retry attempts."""
        from email_campaign import send_email
        
        mock_manager = Mock()
        mock_manager.send_email.return_value = False
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@honestpharmco.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            result = send_email("recipient@example.com", "John", max_retries=3)
            
            assert result is False
            assert mock_manager.send_email.call_count == 3

    def test_send_email_authentication_error_retry(self):
        """Test email sending retries on authentication error."""
        from email_campaign import send_email
        
        mock_manager = Mock()
        # First call raises AuthenticationError, second succeeds
        mock_manager.send_email.side_effect = [
            AuthenticationError("Auth failed", AuthenticationProvider.MAILERSEND, "AUTH_ERROR"),
            True
        ]
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@honestpharmco.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            result = send_email("recipient@example.com", "John", max_retries=3)
            
            assert result is True
            assert mock_manager.send_email.call_count == 2

    def test_send_email_network_error_retry(self):
        """Test email sending retries on network error."""
        from email_campaign import send_email
        
        mock_manager = Mock()
        # First call raises NetworkError, second succeeds
        mock_manager.send_email.side_effect = [
            NetworkError("Network timeout", AuthenticationProvider.MAILERSEND, "NETWORK_ERROR"),
            True
        ]
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@honestpharmco.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            result = send_email("recipient@example.com", "John", max_retries=3)
            
            assert result is True
            assert mock_manager.send_email.call_count == 2

    def test_send_email_generic_exception_retry(self):
        """Test email sending retries on generic exception."""
        from email_campaign import send_email
        
        mock_manager = Mock()
        # First call raises generic Exception, second succeeds
        mock_manager.send_email.side_effect = [
            Exception("Generic error"),
            True
        ]
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@honestpharmco.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            result = send_email("recipient@example.com", "John", max_retries=3)
            
            assert result is True
            assert mock_manager.send_email.call_count == 2

    def test_send_email_authentication_manager_unavailable(self):
        """Test email sending fails when authentication manager is unavailable."""
        from email_campaign import send_email
        
        with patch('email_campaign.auth_manager', None):
            
            result = send_email("recipient@example.com", "John")
            
            assert result is False

    def test_send_email_exponential_backoff_timing(self):
        """Test email sending uses exponential backoff for retries."""
        from email_campaign import send_email
        
        mock_manager = Mock()
        mock_manager.send_email.side_effect = [
            AuthenticationError("Auth failed", AuthenticationProvider.MAILERSEND, "AUTH_ERROR"),
            AuthenticationError("Auth failed", AuthenticationProvider.MAILERSEND, "AUTH_ERROR"),
            True
        ]
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@honestpharmco.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('time.sleep') as mock_sleep:
            
            result = send_email("recipient@example.com", "John", max_retries=3)
            
            assert result is True
            # Check exponential backoff: 2^0=1, 2^1=2
            expected_calls = [((1,),), ((2,),)]
            mock_sleep.assert_has_calls(expected_calls)

    def test_send_email_first_name_processing(self):
        """Test email sending processes first name correctly."""
        from email_campaign import send_email
        
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@honestpharmco.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('email_campaign.get_first_name') as mock_get_first_name:
            
            mock_get_first_name.return_value = "ProcessedName"
            
            result = send_email("recipient@example.com", "John Doe")
            
            assert result is True
            mock_get_first_name.assert_called_once_with("John Doe")
            # Check that processed name is used in email body
            call_args = mock_manager.send_email.call_args
            assert "ProcessedName" in call_args[1]['body']

    def test_send_email_personalized_content(self):
        """Test email sending includes personalized content."""
        from email_campaign import send_email
        
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@honestpharmco.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("recipient@example.com", "John")
            
            assert result is True
            call_args = mock_manager.send_email.call_args
            email_body = call_args[1]['body']
            
            # Check personalization
            assert "Hi John," in email_body
            # Check company branding
            assert "Honest Pharmco" in email_body
            # Check key selling points
            assert "Premium Quality" in email_body
            assert "Competitive Pricing" in email_body


class TestReadContactsFromCSVFunction:
    """Test suite for read_contacts_from_csv() function."""

    def test_read_contacts_valid_csv(self):
        """Test reading contacts from valid CSV file."""
        from email_campaign import read_contacts_from_csv
        
        csv_content = """Primary Contact Name,Email
John Doe,john@example.com
Jane Smith,jane@example.com
Bob Johnson,bob@example.com"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            contacts = read_contacts_from_csv("test.csv")
            
            assert len(contacts) == 3
            assert contacts[0]['email'] == 'john@example.com'
            assert contacts[0]['contact_name'] == 'John Doe'
            assert contacts[0]['first_name'] == 'John'

    def test_read_contacts_csv_with_invalid_emails(self):
        """Test reading CSV file with some invalid email addresses."""
        from email_campaign import read_contacts_from_csv
        
        csv_content = """Primary Contact Name,Email
John Doe,john@example.com
Jane Smith,invalid-email
Bob Johnson,bob@example.com
Alice Brown,"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            contacts = read_contacts_from_csv("test.csv")
            
            # Should only include valid emails
            assert len(contacts) == 2
            assert contacts[0]['email'] == 'john@example.com'
            assert contacts[1]['email'] == 'bob@example.com'

    def test_read_contacts_empty_csv(self):
        """Test reading empty CSV file."""
        from email_campaign import read_contacts_from_csv
        
        csv_content = """Primary Contact Name,Email"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            contacts = read_contacts_from_csv("test.csv")
            
            assert len(contacts) == 0

    def test_read_contacts_missing_file(self):
        """Test reading non-existent CSV file."""
        from email_campaign import read_contacts_from_csv
        
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            contacts = read_contacts_from_csv("nonexistent.csv")
            
            assert contacts == []

    def test_read_contacts_csv_permission_error(self):
        """Test reading CSV file with permission error."""
        from email_campaign import read_contacts_from_csv
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            contacts = read_contacts_from_csv("test.csv")
            
            assert contacts == []

    def test_read_contacts_malformed_csv(self):
        """Test reading malformed CSV file."""
        from email_campaign import read_contacts_from_csv
        
        csv_content = """Primary Contact Name,Email
John Doe,john@example.com
Jane Smith,jane@example.com"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            contacts = read_contacts_from_csv("test.csv")
            
            # Should get valid contacts
            assert len(contacts) == 2
            assert any(contact['email'] == 'john@example.com' for contact in contacts)

    def test_read_contacts_missing_columns(self):
        """Test reading CSV file with missing required columns."""
        from email_campaign import read_contacts_from_csv
        
        csv_content = """Name,Address
John Doe,123 Main St
Jane Smith,456 Oak Ave"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            contacts = read_contacts_from_csv("test.csv")
            
            # Should return empty list when required columns are missing
            assert contacts == []

    def test_read_contacts_empty_rows(self):
        """Test reading CSV file with empty rows."""
        from email_campaign import read_contacts_from_csv
        
        csv_content = """Primary Contact Name,Email
John Doe,john@example.com

Jane Smith,jane@example.com
,
Bob Johnson,bob@example.com"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            contacts = read_contacts_from_csv("test.csv")
            
            # Should skip empty rows
            assert len(contacts) == 3
            assert all(contact['email'] for contact in contacts)

    def test_read_contacts_whitespace_handling(self):
        """Test reading CSV file with whitespace in data."""
        from email_campaign import read_contacts_from_csv
        
        csv_content = """Primary Contact Name,Email
  John Doe  ,  john@example.com  
Jane Smith,jane@example.com"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            contacts = read_contacts_from_csv("test.csv")
            
            assert len(contacts) == 2
            assert contacts[0]['contact_name'] == 'John Doe'  # Whitespace stripped
            assert contacts[0]['email'] == 'john@example.com'  # Whitespace stripped

    def test_read_contacts_encoding_handling(self):
        """Test reading CSV file with UTF-8 encoding."""
        from email_campaign import read_contacts_from_csv
        
        csv_content = """Primary Contact Name,Email
José García,jose@example.com
François Müller,francois@example.com"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            contacts = read_contacts_from_csv("test.csv")
            
            assert len(contacts) == 2
            assert contacts[0]['contact_name'] == 'José García'
            assert contacts[0]['first_name'] == 'José'

    def test_read_contacts_first_name_extraction(self):
        """Test that first names are correctly extracted from contact names."""
        from email_campaign import read_contacts_from_csv
        
        csv_content = """Primary Contact Name,Email
Dr. Michael Johnson,michael@example.com
Mrs. Sarah Wilson,sarah@example.com
John,john@example.com"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)), \
             patch('email_campaign.get_first_name') as mock_get_first_name:
            
            mock_get_first_name.side_effect = lambda name: name.split()[0] if name else "Friend"
            
            contacts = read_contacts_from_csv("test.csv")
            
            assert len(contacts) == 3
            # Verify get_first_name was called for each contact
            assert mock_get_first_name.call_count == 3


class TestSendBatchEmailsFunction:
    """Test suite for send_batch_emails() function."""

    @pytest.fixture
    def sample_contacts(self):
        """Sample contacts for testing."""
        return [
            {"email": "john@example.com", "first_name": "John", "contact_name": "John Doe"},
            {"email": "jane@example.com", "first_name": "Jane", "contact_name": "Jane Smith"},
            {"email": "bob@example.com", "first_name": "Bob", "contact_name": "Bob Johnson"},
            {"email": "alice@example.com", "first_name": "Alice", "contact_name": "Alice Brown"},
            {"email": "charlie@example.com", "first_name": "Charlie", "contact_name": "Charlie Wilson"}
        ]

    def test_send_batch_emails_success(self, sample_contacts):
        """Test successful batch email sending."""
        from email_campaign import send_batch_emails
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            mock_send_email.return_value = True
            
            successful_sends, end_index = send_batch_emails(sample_contacts, 0, 3)
            
            assert successful_sends == 3
            assert end_index == 3
            assert mock_send_email.call_count == 3

    def test_send_batch_emails_partial_success(self, sample_contacts):
        """Test batch email sending with some failures."""
        from email_campaign import send_batch_emails
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            # First and third emails succeed, second fails
            mock_send_email.side_effect = [True, False, True]
            
            successful_sends, end_index = send_batch_emails(sample_contacts, 0, 3)
            
            assert successful_sends == 2
            assert end_index == 3
            assert mock_send_email.call_count == 3

    def test_send_batch_emails_all_failures(self, sample_contacts):
        """Test batch email sending with all failures."""
        from email_campaign import send_batch_emails
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            mock_send_email.return_value = False
            
            successful_sends, end_index = send_batch_emails(sample_contacts, 0, 3)
            
            assert successful_sends == 0
            assert end_index == 3
            assert mock_send_email.call_count == 3

    def test_send_batch_emails_batch_size_larger_than_contacts(self, sample_contacts):
        """Test batch email sending when batch size is larger than remaining contacts."""
        from email_campaign import send_batch_emails
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            mock_send_email.return_value = True
            
            # Start at index 3, batch size 5, but only 2 contacts remaining
            successful_sends, end_index = send_batch_emails(sample_contacts, 3, 5)
            
            assert successful_sends == 2  # Only 2 contacts processed
            assert end_index == 5  # End index is total length
            assert mock_send_email.call_count == 2

    def test_send_batch_emails_empty_batch(self):
        """Test batch email sending with empty contact list."""
        from email_campaign import send_batch_emails
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            successful_sends, end_index = send_batch_emails([], 0, 3)
            
            assert successful_sends == 0
            assert end_index == 0
            assert mock_send_email.call_count == 0

    def test_send_batch_emails_start_index_beyond_contacts(self, sample_contacts):
        """Test batch email sending with start index beyond contact list."""
        from email_campaign import send_batch_emails
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            successful_sends, end_index = send_batch_emails(sample_contacts, 10, 3)
            
            assert successful_sends == 0
            assert end_index == 5  # min(10 + 3, 5) = 5 (length of contacts)
            assert mock_send_email.call_count == 0

    def test_send_batch_emails_delay_between_emails(self, sample_contacts):
        """Test that there's a delay between individual emails in a batch."""
        from email_campaign import send_batch_emails
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep') as mock_sleep:
            
            mock_send_email.return_value = True
            
            send_batch_emails(sample_contacts, 0, 3)
            
            # Should have 3 sleep calls (one after each email)
            assert mock_sleep.call_count == 3
            # Each sleep should be 1 second
            for call in mock_sleep.call_args_list:
                assert call[0][0] == 1

    def test_send_batch_emails_correct_contact_data(self, sample_contacts):
        """Test that correct contact data is passed to send_email function."""
        from email_campaign import send_batch_emails
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):  # Mock sleep to speed up test
            
            mock_send_email.return_value = True
            
            send_batch_emails(sample_contacts, 1, 2)  # Process contacts 1 and 2
            
            assert mock_send_email.call_count == 2
            
            # Check first call (contact index 1)
            first_call = mock_send_email.call_args_list[0]
            assert first_call[0][0] == "jane@example.com"
            assert first_call[0][1] == "Jane"
            
            # Check second call (contact index 2)
            second_call = mock_send_email.call_args_list[1]
            assert second_call[0][0] == "bob@example.com"
            assert second_call[0][1] == "Bob"

    def test_send_batch_emails_batch_numbering_display(self, sample_contacts):
        """Test that batch numbering is displayed correctly."""
        from email_campaign import send_batch_emails
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'), \
             patch('builtins.print') as mock_print:  # Mock print to capture output
            
            mock_send_email.return_value = True
            
            send_batch_emails(sample_contacts, 3, 2)  # Start at index 3, batch size 2
            
            # Should print batch information
            mock_print.assert_called()
            # Check that batch number calculation is correct (batch 2: (3//2 + 1) = 2)
            print_calls = [str(call) for call in mock_print.call_args_list]
            batch_info_found = any("batch 2" in call.lower() for call in print_calls)
            assert batch_info_found


class TestEmailCampaignIntegrationScenarios:
    """Test suite for integration scenarios between campaign functions."""

    def test_full_contact_processing_workflow(self):
        """Test complete workflow from CSV reading to batch sending."""
        from email_campaign import read_contacts_from_csv, send_batch_emails
        
        csv_content = """Primary Contact Name,Email
John Doe,john@example.com
Jane Smith,jane@example.com
Bob Johnson,bob@example.com"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)), \
             patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):
            
            mock_send_email.return_value = True
            
            # Read contacts from CSV
            contacts = read_contacts_from_csv("test.csv")
            assert len(contacts) == 3
            
            # Send batch emails
            successful_sends, end_index = send_batch_emails(contacts, 0, 2)
            
            assert successful_sends == 2
            assert end_index == 2
            assert mock_send_email.call_count == 2

    def test_error_recovery_in_batch_processing(self):
        """Test error recovery during batch processing."""
        from email_campaign import send_batch_emails
        
        contacts = [
            {"email": "john@example.com", "first_name": "John", "contact_name": "John Doe"},
            {"email": "jane@example.com", "first_name": "Jane", "contact_name": "Jane Smith"},
            {"email": "bob@example.com", "first_name": "Bob", "contact_name": "Bob Johnson"}
        ]
        
        with patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):
            
            # Second email fails, others succeed
            mock_send_email.side_effect = [True, False, True]
            
            successful_sends, end_index = send_batch_emails(contacts, 0, 3)
            
            # Should continue processing despite failure
            assert successful_sends == 2
            assert end_index == 3
            assert mock_send_email.call_count == 3

    def test_name_processing_consistency(self):
        """Test that name processing is consistent across functions."""
        from email_campaign import get_first_name, read_contacts_from_csv
        
        csv_content = """Primary Contact Name,Email
Dr. Michael Johnson,michael@example.com"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            contacts = read_contacts_from_csv("test.csv")
            
            # First name should be processed consistently
            direct_result = get_first_name("Dr. Michael Johnson")
            csv_result = contacts[0]['first_name']
            
            assert direct_result == csv_result
            assert csv_result == "Michael"  # Title should be removed


# Mark tests for pytest
pytest.mark.email_campaign = pytest.mark.email_campaign
pytest.mark.unit = pytest.mark.unit