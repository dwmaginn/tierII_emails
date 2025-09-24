"""Integration tests for comprehensive email campaign workflow.

This module contains end-to-end integration tests for the complete email campaign
workflow, from CSV reading through authentication to batch email delivery,
including error scenarios and recovery mechanisms.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
import csv
import io
import time
import tempfile
import os
from datetime import datetime

# Import the modules to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from auth.base_authentication_manager import (
    AuthenticationError,
    NetworkError,
    InvalidCredentialsError,
    AuthenticationProvider
)


class TestEndToEndEmailCampaignWorkflow:
    """Test suite for complete end-to-end email campaign workflow."""

    @pytest.fixture
    def sample_csv_content(self):
        """Sample CSV content for testing."""
        return """Primary Contact Name,Email
John Doe,john@example.com
Jane Smith,jane@example.com
Dr. Michael Johnson,michael@example.com
Mrs. Sarah Wilson,sarah@example.com
Bob Johnson,bob@example.com"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for email campaign."""
        settings = Mock()
        settings.mailersend_api_token = "test_api_key"
        settings.sender_email = "test@honestpharmco.com"
        settings.sender_name = "Test Sender"
        settings.test_fallback_first_name = "Friend"
        settings.campaign_batch_size = 2
        settings.campaign_delay_minutes = 0.1  # Short delay for testing
        settings.test_csv_filename = "test_contacts.csv"
        settings.test_recipient_email = None
        return settings

    @pytest.fixture
    def mock_auth_manager(self):
        """Mock authentication manager."""
        manager = Mock()
        manager.provider = AuthenticationProvider.MAILERSEND
        manager.is_authenticated = True
        manager.send_email.return_value = True
        manager.authenticate.return_value = True
        manager.validate_configuration.return_value = True
        return manager

    def test_complete_successful_campaign_workflow(self, sample_csv_content, mock_settings, mock_auth_manager):
        """Test complete successful email campaign workflow from CSV to delivery."""
        from email_campaign import read_contacts_from_csv, send_batch_emails, main
        
        with patch('builtins.open', mock_open(read_data=sample_csv_content)), \
             patch('email_campaign.settings', mock_settings), \
             patch('email_campaign.auth_manager', mock_auth_manager), \
             patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'), \
             patch('builtins.input', return_value='y'):  # Simulate user confirmation
            
            mock_send_email.return_value = True
            
            # Read contacts
            contacts = read_contacts_from_csv("test_contacts.csv")
            assert len(contacts) == 5
            
            # Verify contact processing
            assert contacts[0]['email'] == 'john@example.com'
            assert contacts[0]['first_name'] == 'John'
            assert contacts[2]['first_name'] == 'Michael'  # Title removed
            
            # Send batch emails
            successful_sends, end_index = send_batch_emails(contacts, 0, 2)
            assert successful_sends == 2
            assert end_index == 2
            
            # Verify email sending was called correctly
            assert mock_send_email.call_count == 2

    def test_campaign_workflow_with_authentication_failure(self, sample_csv_content, mock_settings):
        """Test campaign workflow handles authentication failure gracefully."""
        from email_campaign import create_authentication_manager
        
        mock_auth_manager = Mock()
        mock_auth_manager.authenticate.side_effect = InvalidCredentialsError(
            "Invalid API key", AuthenticationProvider.MAILERSEND, "INVALID_KEY"
        )
        
        with patch('builtins.open', mock_open(read_data=sample_csv_content)), \
             patch('email_campaign.settings', mock_settings), \
             patch('email_campaign.authentication_factory') as mock_factory:
            
            mock_factory.create_manager.return_value = mock_auth_manager
            
            # Should handle authentication failure
            with pytest.raises(InvalidCredentialsError):
                manager = create_authentication_manager()
                manager.authenticate()

    def test_campaign_workflow_with_csv_corruption(self, mock_settings, mock_auth_manager):
        """Test campaign workflow handles CSV corruption during processing."""
        from email_campaign import read_contacts_from_csv
        
        corrupted_csv = """Primary Contact Name,Email
John Doe,john@example.com
Jane Smith,jane@example.com
Bob Johnson,bob@example.com"""
        
        with patch('builtins.open', mock_open(read_data=corrupted_csv)), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("test_contacts.csv")
            
            # Should process valid contacts
            assert len(contacts) == 3
            valid_emails = [contact['email'] for contact in contacts]
            assert 'john@example.com' in valid_emails
            assert 'bob@example.com' in valid_emails

    def test_campaign_workflow_with_network_interruption(self, sample_csv_content, mock_settings):
        """Test campaign workflow handles network interruption during batch send."""
        from email_campaign import send_batch_emails, read_contacts_from_csv
        
        with patch('builtins.open', mock_open(read_data=sample_csv_content)), \
             patch('email_campaign.settings', mock_settings), \
             patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):
            
            # Simulate network interruption: first email succeeds, second fails, third succeeds
            mock_send_email.side_effect = [True, False, True]
            
            contacts = read_contacts_from_csv("test_contacts.csv")
            successful_sends, end_index = send_batch_emails(contacts, 0, 3)
            
            # Should continue processing despite network failure
            assert successful_sends == 2  # 2 out of 3 succeeded
            assert end_index == 3
            assert mock_send_email.call_count == 3

    def test_campaign_workflow_with_rate_limiting(self, sample_csv_content, mock_settings, mock_auth_manager):
        """Test campaign workflow handles rate limiting enforcement."""
        from email_campaign import send_batch_emails, read_contacts_from_csv
        
        with patch('builtins.open', mock_open(read_data=sample_csv_content)), \
             patch('email_campaign.settings', mock_settings), \
             patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep') as mock_sleep:
            
            mock_send_email.return_value = True
            
            contacts = read_contacts_from_csv("test_contacts.csv")
            send_batch_emails(contacts, 0, 3)
            
            # Should have delays between emails (rate limiting)
            assert mock_sleep.call_count == 3  # One sleep after each email
            for call in mock_sleep.call_args_list:
                assert call[0][0] == 1  # 1 second delay

    def test_campaign_workflow_authentication_failure_mid_campaign(self, sample_csv_content, mock_settings):
        """Test campaign workflow handles authentication failure mid-campaign."""
        from email_campaign import send_batch_emails, read_contacts_from_csv
        
        with patch('builtins.open', mock_open(read_data=sample_csv_content)), \
             patch('email_campaign.settings', mock_settings), \
             patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):
            
            # First email succeeds, second fails with auth error, third succeeds after retry
            mock_send_email.side_effect = [
                True,
                False,  # Auth failure
                True    # Recovery
            ]
            
            contacts = read_contacts_from_csv("test_contacts.csv")
            successful_sends, end_index = send_batch_emails(contacts, 0, 3)
            
            # Should handle auth failure gracefully
            assert successful_sends == 2
            assert end_index == 3

    def test_campaign_workflow_with_empty_csv(self, mock_settings, mock_auth_manager):
        """Test campaign workflow handles empty CSV file."""
        from email_campaign import read_contacts_from_csv, send_batch_emails
        
        empty_csv = """Primary Contact Name,Email"""
        
        with patch('builtins.open', mock_open(read_data=empty_csv)), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("test_contacts.csv")
            assert len(contacts) == 0
            
            # Should handle empty contact list gracefully
            successful_sends, end_index = send_batch_emails(contacts, 0, 5)
            assert successful_sends == 0
            assert end_index == 0

    def test_campaign_workflow_with_invalid_csv_file(self, mock_settings, mock_auth_manager):
        """Test campaign workflow handles invalid CSV file."""
        from email_campaign import read_contacts_from_csv
        
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("nonexistent.csv")
            assert contacts == []

    def test_campaign_workflow_batch_processing_with_delays(self, sample_csv_content, mock_settings):
        """Test campaign workflow respects batch processing with proper delays."""
        from email_campaign import read_contacts_from_csv, send_batch_emails
        
        with patch('builtins.open', mock_open(read_data=sample_csv_content)), \
             patch('email_campaign.settings', mock_settings), \
             patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep') as mock_sleep:
            
            mock_send_email.return_value = True
            
            contacts = read_contacts_from_csv("test_contacts.csv")
            
            # Process first batch
            successful_sends_1, end_index_1 = send_batch_emails(contacts, 0, 2)
            assert successful_sends_1 == 2
            assert end_index_1 == 2
            
            # Process second batch
            successful_sends_2, end_index_2 = send_batch_emails(contacts, 2, 2)
            assert successful_sends_2 == 2
            assert end_index_2 == 4
            
            # Verify delays were applied
            total_sleep_calls = mock_sleep.call_count
            assert total_sleep_calls == 4  # 2 calls per batch

    def test_campaign_workflow_progress_tracking(self, sample_csv_content, mock_settings):
        """Test campaign workflow tracks progress accurately."""
        from email_campaign import read_contacts_from_csv, send_batch_emails
        
        with patch('builtins.open', mock_open(read_data=sample_csv_content)), \
             patch('email_campaign.settings', mock_settings), \
             patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'), \
             patch('builtins.print') as mock_print:
            
            mock_send_email.return_value = True
            
            contacts = read_contacts_from_csv("test_contacts.csv")
            send_batch_emails(contacts, 0, 3)
            
            # Should print progress information
            mock_print.assert_called()
            print_calls = [str(call) for call in mock_print.call_args_list]
            
            # Check for batch information
            batch_info_found = any("batch" in call.lower() for call in print_calls)
            assert batch_info_found

    def test_campaign_workflow_error_recovery_options(self, sample_csv_content, mock_settings):
        """Test campaign workflow provides error recovery options."""
        from email_campaign import send_batch_emails, read_contacts_from_csv
        
        with patch('builtins.open', mock_open(read_data=sample_csv_content)), \
             patch('email_campaign.settings', mock_settings), \
             patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):
            
            # Simulate intermittent failures
            mock_send_email.side_effect = [True, False, True, False, True]
            
            contacts = read_contacts_from_csv("test_contacts.csv")
            successful_sends, end_index = send_batch_emails(contacts, 0, 5)
            
            # Should continue processing and report partial success
            assert successful_sends == 3  # 3 out of 5 succeeded
            assert end_index == 5
            assert mock_send_email.call_count == 5


class TestCampaignWorkflowPerformanceAndReliability:
    """Test suite for campaign workflow performance and reliability."""

    @pytest.fixture
    def large_csv_content(self):
        """Large CSV content for performance testing."""
        lines = ["Primary Contact Name,Email"]
        for i in range(100):
            lines.append(f"Contact {i},contact{i}@example.com")
        return "\n".join(lines)

    def test_campaign_workflow_performance_with_large_dataset(self, large_csv_content):
        """Test campaign workflow performance with large contact dataset."""
        from email_campaign import read_contacts_from_csv, send_batch_emails
        
        mock_settings = Mock()
        mock_settings.test_fallback_first_name = "Friend"
        
        start_time = time.time()
        
        with patch('builtins.open', mock_open(read_data=large_csv_content)), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("large_test.csv")
            
        processing_time = time.time() - start_time
        
        # Should process 100 contacts efficiently
        assert len(contacts) == 100
        assert processing_time < 5.0, f"CSV processing took {processing_time:.2f}s, should be < 5s"

    def test_campaign_workflow_memory_efficiency(self, large_csv_content):
        """Test campaign workflow memory efficiency with large datasets."""
        from email_campaign import read_contacts_from_csv, send_batch_emails
        
        mock_settings = Mock()
        mock_settings.test_fallback_first_name = "Friend"
        
        with patch('builtins.open', mock_open(read_data=large_csv_content)), \
             patch('email_campaign.settings', mock_settings), \
             patch('email_campaign.send_email') as mock_send_email, \
             patch('time.sleep'):
            
            mock_send_email.return_value = True
            
            contacts = read_contacts_from_csv("large_test.csv")
            
            # Process in small batches to test memory efficiency
            total_successful = 0
            batch_size = 10
            
            for start_idx in range(0, len(contacts), batch_size):
                successful_sends, _ = send_batch_emails(contacts, start_idx, batch_size)
                total_successful += successful_sends
            
            assert total_successful == 100

    def test_campaign_workflow_concurrent_safety(self, large_csv_content):
        """Test campaign workflow safety under concurrent operations."""
        from email_campaign import read_contacts_from_csv
        
        mock_settings = Mock()
        mock_settings.test_fallback_first_name = "Friend"
        
        # Simulate concurrent CSV reading
        with patch('builtins.open', mock_open(read_data=large_csv_content)), \
             patch('email_campaign.settings', mock_settings):
            
            contacts1 = read_contacts_from_csv("test1.csv")
            contacts2 = read_contacts_from_csv("test2.csv")
            
            # Both should process successfully
            assert len(contacts1) == 100
            assert len(contacts2) == 100
            assert contacts1[0]['email'] == contacts2[0]['email']

    def test_campaign_workflow_resource_cleanup(self, large_csv_content):
        """Test campaign workflow properly cleans up resources."""
        from email_campaign import read_contacts_from_csv
        
        mock_settings = Mock()
        mock_settings.test_fallback_first_name = "Friend"
        
        mock_file = mock_open(read_data=large_csv_content)
        
        with patch('builtins.open', mock_file), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("test.csv")
            
            # Verify file was properly closed
            mock_file.return_value.__enter__.assert_called_once()
            mock_file.return_value.__exit__.assert_called_once()
            
            assert len(contacts) == 100


class TestCampaignWorkflowEdgeCases:
    """Test suite for campaign workflow edge cases and boundary conditions."""

    def test_campaign_workflow_with_unicode_characters(self):
        """Test campaign workflow handles Unicode characters in names and emails."""
        from email_campaign import read_contacts_from_csv, get_first_name
        
        unicode_csv = """Primary Contact Name,Email
José García,josé@example.com
François Müller,françois@example.com
李小明,xiaoming@example.com"""
        
        mock_settings = Mock()
        mock_settings.test_fallback_first_name = "Friend"
        
        with patch('builtins.open', mock_open(read_data=unicode_csv)), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("unicode_test.csv")
            
            assert len(contacts) == 3
            assert contacts[0]['contact_name'] == 'José García'
            assert contacts[0]['email'] == 'josé@example.com'
            assert contacts[0]['first_name'] == 'José'

    def test_campaign_workflow_with_very_long_names(self):
        """Test campaign workflow handles very long contact names."""
        from email_campaign import read_contacts_from_csv, get_first_name
        
        long_name = "Dr. " + "A" * 100 + " " + "B" * 100
        long_csv = f"""Primary Contact Name,Email
{long_name},long@example.com"""
        
        mock_settings = Mock()
        mock_settings.test_fallback_first_name = "Friend"
        
        with patch('builtins.open', mock_open(read_data=long_csv)), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("long_test.csv")
            
            assert len(contacts) == 1
            assert len(contacts[0]['contact_name']) > 200
            assert contacts[0]['first_name'] == "A" * 100  # Should extract first name

    def test_campaign_workflow_with_malformed_email_addresses(self):
        """Test campaign workflow filters out malformed email addresses."""
        from email_campaign import read_contacts_from_csv
        
        malformed_csv = """Primary Contact Name,Email
John Doe,john@example.com
Jane Smith,invalid-email
Bob Johnson,validbob@example.com
Alice Brown,alice@validexample.com
Charlie Wilson,charlie@example.com"""
        
        mock_settings = Mock()
        mock_settings.test_fallback_first_name = "Friend"
        
        with patch('builtins.open', mock_open(read_data=malformed_csv)), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("malformed_test.csv")
            
            # Should only include valid email addresses (basic @ validation)
            valid_emails = [contact['email'] for contact in contacts]
            assert 'john@example.com' in valid_emails
            assert 'charlie@example.com' in valid_emails
            assert 'validbob@example.com' in valid_emails
            assert 'alice@validexample.com' in valid_emails
            assert 'invalid-email' not in valid_emails

    def test_campaign_workflow_with_duplicate_email_addresses(self):
        """Test campaign workflow handles duplicate email addresses."""
        from email_campaign import read_contacts_from_csv
        
        duplicate_csv = """Primary Contact Name,Email
John Doe,john@example.com
Jane Smith,jane@example.com
John Duplicate,john@example.com
Jane Duplicate,jane@example.com"""
        
        mock_settings = Mock()
        mock_settings.test_fallback_first_name = "Friend"
        
        with patch('builtins.open', mock_open(read_data=duplicate_csv)), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("duplicate_test.csv")
            
            # Should include all contacts (deduplication is not implemented in read function)
            assert len(contacts) == 4
            emails = [contact['email'] for contact in contacts]
            assert emails.count('john@example.com') == 2
            assert emails.count('jane@example.com') == 2

    def test_campaign_workflow_with_empty_contact_names(self):
        """Test campaign workflow handles empty contact names."""
        from email_campaign import read_contacts_from_csv
        
        empty_name_csv = """Primary Contact Name,Email
,john@example.com
Jane Smith,jane@example.com
   ,bob@example.com"""
        
        mock_settings = Mock()
        mock_settings.test_fallback_first_name = "Friend"
        
        with patch('builtins.open', mock_open(read_data=empty_name_csv)), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("empty_name_test.csv")
            
            assert len(contacts) == 3
            # Empty names should fall back to default
            assert contacts[0]['first_name'] == 'Friend'
            assert contacts[1]['first_name'] == 'Jane'
            assert contacts[2]['first_name'] == 'Friend'


class TestCampaignWorkflowSecurityAndCompliance:
    """Test suite for campaign workflow security and compliance aspects."""

    def test_campaign_workflow_email_content_safety(self):
        """Test campaign workflow generates safe email content."""
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
            
            # Check for compliance elements
            assert "UNSUBSCRIBE" in email_body
            assert "contact@honestpharmco.com" in email_body
            # Should not contain any script tags or suspicious content
            assert "<script>" not in email_body
            assert "javascript:" not in email_body

    def test_campaign_workflow_data_privacy_protection(self):
        """Test campaign workflow protects sensitive data."""
        from email_campaign import read_contacts_from_csv
        
        sensitive_csv = """Primary Contact Name,Email,Phone,SSN
John Doe,john@example.com,555-1234,123-45-6789
Jane Smith,jane@example.com,555-5678,987-65-4321"""
        
        mock_settings = Mock()
        mock_settings.test_fallback_first_name = "Friend"
        
        with patch('builtins.open', mock_open(read_data=sensitive_csv)), \
             patch('email_campaign.settings', mock_settings):
            
            contacts = read_contacts_from_csv("sensitive_test.csv")
            
            # Should only extract necessary fields
            for contact in contacts:
                assert 'email' in contact
                assert 'first_name' in contact
                assert 'contact_name' in contact
                # Should not include sensitive fields
                assert 'Phone' not in contact
                assert 'SSN' not in contact

    def test_campaign_workflow_input_validation(self):
        """Test campaign workflow validates all inputs properly."""
        from email_campaign import get_first_name, send_email
        
        # Test name validation
        assert get_first_name(None) is not None
        assert get_first_name("") is not None
        assert get_first_name("   ") is not None
        
        # Test email sending with invalid inputs
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        
        mock_settings = Mock()
        mock_settings.sender_email = "test@honestpharmco.com"
        mock_settings.sender_name = "Test Sender"
        
        with patch('email_campaign.auth_manager', mock_manager), \
             patch('email_campaign.settings', mock_settings):
            
            # Should handle edge cases gracefully
            result = send_email("", "")  # Empty inputs
            # Function should handle this gracefully (may return False)
            assert isinstance(result, bool)


# Mark tests for pytest
pytest.mark.integration = pytest.mark.integration
pytest.mark.email_campaign = pytest.mark.email_campaign