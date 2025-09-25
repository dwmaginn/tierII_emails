"""Unit tests for email_campaign.py MailerSend integration.

Tests the integration of MailerSend authentication with email_campaign.py,
including error handling and retry logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
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
    NetworkError
)

# Import functions at module level to avoid repeated imports in tests
try:
    from email_campaign import send_email
    import email_campaign
    print("Successfully imported email_campaign functions")
except ImportError as e:
    print(f"Failed to import email_campaign functions: {e}")
    send_email = None


class TestEmailCampaignMailerSendIntegration:
    """Test cases for email campaign MailerSend integration."""

    @pytest.fixture
    def mock_mailersend_manager(self):
        """Create a mock MailerSend authentication manager."""
        manager = Mock()
        manager.provider = AuthenticationProvider.MAILERSEND
        manager.is_authenticated = True
        manager.send_email.return_value = True
        return manager

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.sender_email = "test@example.com"
        settings.sender_name = "Test Sender"
        settings.test_fallback_first_name = "Friend"
        return settings

    @pytest.mark.skipif(send_email is None, reason="email_campaign module not available")
    def test_send_email_mailersend_success(self, mock_mailersend_manager, mock_settings):
        """Test successful email sending via MailerSend."""
        with patch('email_campaign.auth_manager', mock_mailersend_manager), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("test@example.com", "John")
            
            assert result is True
            mock_mailersend_manager.send_email.assert_called_once()
            call_args = mock_mailersend_manager.send_email.call_args
            assert call_args[1]['to_email'] == "test@example.com"
            assert 'subject' in call_args[1]
            assert 'html_content' in call_args[1]

    @pytest.mark.skipif(send_email is None, reason="email_campaign module not available")
    def test_send_email_authentication_error(self, mock_mailersend_manager, mock_settings):
        """Test email sending with authentication error."""
        mock_mailersend_manager.send_email.side_effect = AuthenticationError("Auth failed", AuthenticationProvider.MAILERSEND)
        
        with patch('email_campaign.auth_manager', mock_mailersend_manager), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("test@example.com", "John")
            
            assert result is False

    @pytest.mark.skipif(send_email is None, reason="email_campaign module not available")
    def test_send_email_network_error(self, mock_mailersend_manager, mock_settings):
        """Test email sending with network error."""
        mock_mailersend_manager.send_email.side_effect = NetworkError("Network failed", AuthenticationProvider.MAILERSEND)
        
        with patch('email_campaign.auth_manager', mock_mailersend_manager), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("test@example.com", "John")
            
            assert result is False

    @pytest.mark.skipif(send_email is None, reason="email_campaign module not available")
    def test_send_email_retry_logic(self, mock_mailersend_manager, mock_settings):
        """Test email sending retry logic with exponential backoff."""
        # First two attempts fail, third succeeds
        mock_mailersend_manager.send_email.side_effect = [
            AuthenticationError("Auth failed", AuthenticationProvider.MAILERSEND),
            NetworkError("Network failed", AuthenticationProvider.MAILERSEND),
            True
        ]
        
        with patch('email_campaign.auth_manager', mock_mailersend_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('time.sleep') as mock_sleep:
            
            result = send_email("test@example.com", "John", max_retries=3)
            
            assert result is True
            assert mock_mailersend_manager.send_email.call_count == 3
            # Verify exponential backoff was used
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1)  # 2^0
            mock_sleep.assert_any_call(2)  # 2^1

    @pytest.mark.skipif(send_email is None, reason="email_campaign module not available")
    def test_send_email_max_retries_exceeded(self, mock_mailersend_manager, mock_settings):
        """Test email sending when max retries are exceeded."""
        mock_mailersend_manager.send_email.side_effect = AuthenticationError("Auth failed", AuthenticationProvider.MAILERSEND)
        
        with patch('email_campaign.auth_manager', mock_mailersend_manager), \
             patch('email_campaign.settings', mock_settings), \
             patch('time.sleep'):
            
            result = send_email("test@example.com", "John", max_retries=2)
            
            assert result is False
            assert mock_mailersend_manager.send_email.call_count == 2

    @pytest.mark.skipif(send_email is None, reason="email_campaign module not available")
    def test_send_email_no_auth_manager(self, mock_settings):
        """Test email sending when auth manager is None."""
        with patch('email_campaign.auth_manager', None), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("test@example.com", "John")
            
            assert result is False

    @pytest.mark.skipif(send_email is None, reason="email_campaign module not available")
    def test_send_email_personalization(self, mock_mailersend_manager, mock_settings):
        """Test email personalization with first name."""
        with patch('email_campaign.auth_manager', mock_mailersend_manager), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("test@example.com", "Alice")
            
            assert result is True
            call_args = mock_mailersend_manager.send_email.call_args
            body = call_args[1]['html_content']
            assert "Hi Alice," in body

    @pytest.mark.skipif(send_email is None, reason="email_campaign module not available")
    def test_send_email_fallback_first_name(self, mock_mailersend_manager, mock_settings):
        """Test email with fallback first name."""
        with patch('email_campaign.auth_manager', mock_mailersend_manager), \
             patch('email_campaign.settings', mock_settings):
            
            result = send_email("test@example.com", "")
            
            assert result is True
            call_args = mock_mailersend_manager.send_email.call_args
            body = call_args[1]['html_content']
            assert "Hi Friend," in body  # Uses fallback name

    def test_get_first_name_extraction(self):
        """Test first name extraction from contact names."""
        from email_campaign import get_first_name
        
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_fallback_first_name = "Friend"
            
            # Test normal name
            assert get_first_name("John Doe") == "John"
            
            # Test name with title
            assert get_first_name("Mr. John Doe") == "John"
            assert get_first_name("Dr. Jane Smith") == "Jane"
            
            # Test empty name
            assert get_first_name("") == "Friend"
            assert get_first_name(None) == "Friend"
            
            # Test single name
            assert get_first_name("Alice") == "Alice"

    def test_email_campaign_class_integration(self):
        """Test EmailCampaign class integration with MailerSend."""
        from email_campaign import EmailCampaign
        
        with patch('email_campaign.read_contacts_from_csv') as mock_read_csv, \
             patch('email_campaign.send_email') as mock_send_email, \
             patch('email_campaign.settings') as mock_settings:
            
            mock_settings.test_csv_filename = "test.csv"
            mock_settings.campaign_batch_size = 2
            mock_settings.campaign_delay_minutes = 1
            
            mock_read_csv.return_value = [
                {"email": "test1@example.com", "first_name": "John", "contact_name": "John Doe"},
                {"email": "test2@example.com", "first_name": "Jane", "contact_name": "Jane Smith"}
            ]
            mock_send_email.return_value = True
            
            campaign = EmailCampaign()
            contacts_loaded = campaign.load_contacts()
            
            assert contacts_loaded == 2
            assert len(campaign.contacts) == 2
            
            with patch('time.sleep'):
                total_sent = campaign.send_campaign()
            
            assert total_sent == 2
            assert mock_send_email.call_count == 2


class TestEmailCampaignConfiguration:
    """Test email campaign configuration and setup."""

    def test_campaign_initialization_with_settings(self):
        """Test campaign initialization with settings."""
        from email_campaign import EmailCampaign
        
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_csv_filename = "custom.csv"
            mock_settings.campaign_batch_size = 25
            mock_settings.campaign_delay_minutes = 3
            
            campaign = EmailCampaign()
            
            assert campaign.csv_file == "custom.csv"
            assert campaign.batch_size == 25
            assert campaign.delay_minutes == 3

    def test_campaign_initialization_with_overrides(self):
        """Test campaign initialization with parameter overrides."""
        from email_campaign import EmailCampaign
        
        with patch('email_campaign.settings') as mock_settings:
            mock_settings.test_csv_filename = "default.csv"
            
            campaign = EmailCampaign(
                csv_file="override.csv",
                batch_size=10,
                delay_minutes=2
            )
            
            assert campaign.csv_file == "override.csv"
            assert campaign.batch_size == 10
            assert campaign.delay_minutes == 2

    def test_create_authentication_manager(self):
        """Test authentication manager creation."""
        from email_campaign import create_authentication_manager
        
        with patch('email_campaign.settings') as mock_settings, \
             patch('email_campaign.authentication_factory') as mock_factory:
            
            mock_settings.mailersend_api_token = "test_token"
            mock_settings.sender_email = "test@example.com"
            mock_settings.sender_name = "Test Sender"
            
            mock_manager = Mock()
            mock_factory.create_manager.return_value = mock_manager
            
            result = create_authentication_manager()
            
            assert result == mock_manager
            mock_factory.create_manager.assert_called_once_with(
                provider=AuthenticationProvider.MAILERSEND,
                config={
                    "mailersend_api_token": "test_token",
                    "sender_email": "test@example.com",
                    "sender_name": "Test Sender"
                }
            )