"""Integration tests for MailerSend configuration workflows.

These tests verify that the full email workflow functions correctly
with MailerSend configuration while using test data to prevent unintended email sends.
"""

import pytest
from unittest.mock import patch, Mock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestMailerSendWorkflow:
    """Test MailerSend email workflow."""

    @pytest.fixture
    def mailersend_config(self):
        """Provide MailerSend configuration for testing."""
        return {
            'TIERII_SENDER_EMAIL': 'test@honestpharmco.com',
            'TIERII_MAILERSEND_API_TOKEN': 'test-mailersend-token',
            'TIERII_SENDER_NAME': 'Test Sender',
            'TIERII_CAMPAIGN_BATCH_SIZE': '5',
            'TIERII_CAMPAIGN_DELAY_MINUTES': '1',
            'TIERII_TEST_RECIPIENT_EMAIL': 'test@example.com',
            'TIERII_TEST_FALLBACK_FIRST_NAME': 'Friend',
            'TIERII_TEST_CSV_FILENAME': 'data/test/testdata.csv'
        }

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_mailersend_config_loading(self, mailersend_config):
        """Test that MailerSend configuration loads correctly."""
        with patch.dict(os.environ, mailersend_config):
            from config.settings import load_settings

            settings = load_settings()

            # Verify core email settings
            assert settings.sender_email == "test@honestpharmco.com"
            assert settings.mailersend_api_token == "test-mailersend-token"
            assert settings.sender_name == "Test Sender"

            # Verify campaign settings
            assert settings.campaign_batch_size == 5
            assert settings.campaign_delay_minutes == 1

            # Verify test settings
            assert settings.test_recipient_email == "test@example.com"
            assert settings.test_fallback_first_name == "Friend"

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_mailersend_authentication_manager_creation(self, mailersend_config):
        """Test that MailerSend authentication manager is created correctly."""
        with patch.dict(os.environ, mailersend_config):
            from email_campaign import create_authentication_manager
            from auth.base_authentication_manager import AuthenticationProvider

            with patch('email_campaign.authentication_factory') as mock_factory, \
                 patch('email_campaign.settings') as mock_settings:
                
                # Configure mock settings with test values
                mock_settings.mailersend_api_token = "test-mailersend-token"
                mock_settings.sender_email = "test@honestpharmco.com"
                mock_settings.sender_name = "Test Sender"
                
                mock_manager = Mock()
                mock_factory.create_manager.return_value = mock_manager

                manager = create_authentication_manager()

                assert manager == mock_manager
                mock_factory.create_manager.assert_called_once_with(
                    provider=AuthenticationProvider.MAILERSEND,
                    config={
                        "mailersend_api_token": "test-mailersend-token",
                        "sender_email": "test@honestpharmco.com",
                        "sender_name": "Test Sender"
                    }
                )

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_mailersend_email_sending_workflow(self, mailersend_config):
        """Test complete MailerSend email sending workflow."""
        with patch.dict(os.environ, mailersend_config):
            from src.email_campaign import send_email

            # Mock the authentication manager
            mock_manager = Mock()
            mock_manager.send_email.return_value = True

            with patch('src.email_campaign.auth_manager', mock_manager):
                result = send_email("test@example.com", "John")

                assert result is True
                mock_manager.send_email.assert_called_once()
                call_args = mock_manager.send_email.call_args
                assert call_args[1]['recipient_email'] == "test@example.com"
                assert call_args[1]['sender_email'] == "test@honestpharmco.com"
                assert call_args[1]['sender_name'] == "Test Sender"
                assert "Hi John," in call_args[1]['body']

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_mailersend_campaign_workflow(self, mailersend_config):
        """Test complete MailerSend campaign workflow."""
        with patch.dict(os.environ, mailersend_config):
            from src.email_campaign import EmailCampaign

            # Mock CSV reading and email sending
            mock_contacts = [
                {"email": "test1@example.com", "first_name": "John", "contact_name": "John Doe"},
                {"email": "test2@example.com", "first_name": "Jane", "contact_name": "Jane Smith"}
            ]

            with patch('src.email_campaign.read_contacts_from_csv') as mock_read_csv, \
                 patch('src.email_campaign.send_email') as mock_send_email, \
                 patch('time.sleep'):  # Mock sleep to speed up test

                mock_read_csv.return_value = mock_contacts
                mock_send_email.return_value = True

                campaign = EmailCampaign(batch_size=1, delay_minutes=0)
                contacts_loaded = campaign.load_contacts()
                total_sent = campaign.send_campaign()

                assert contacts_loaded == 2
                assert total_sent == 2
                assert mock_send_email.call_count == 2

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_mailersend_error_handling(self, mailersend_config):
        """Test MailerSend error handling in workflow."""
        with patch.dict(os.environ, mailersend_config):
            from src.email_campaign import send_email
            from src.auth.base_authentication_manager import AuthenticationError, AuthenticationProvider

            # Mock authentication manager that fails
            mock_manager = Mock()
            mock_manager.send_email.side_effect = AuthenticationError("API token invalid", AuthenticationProvider.MAILERSEND)

            with patch('src.email_campaign.auth_manager', mock_manager), \
                 patch('time.sleep'):  # Mock sleep to speed up test

                result = send_email("test@example.com", "John", max_retries=2)

                assert result is False
                assert mock_manager.send_email.call_count == 2  # Should retry

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_mailersend_configuration_validation(self, mailersend_config):
        """Test MailerSend configuration validation."""
        # Test with missing API token
        incomplete_config = mailersend_config.copy()
        del incomplete_config['TIERII_MAILERSEND_API_TOKEN']
        
        # Explicitly unset the API token in environment
        env_patch = incomplete_config.copy()
        env_patch['TIERII_MAILERSEND_API_TOKEN'] = ''

        with patch.dict(os.environ, env_patch):
            from config.settings import load_settings

            with pytest.raises(SystemExit):
                load_settings()

        # Test with missing sender email
        incomplete_config = mailersend_config.copy()
        del incomplete_config['TIERII_SENDER_EMAIL']
        
        # Explicitly unset the sender email in environment
        env_patch = incomplete_config.copy()
        env_patch['TIERII_SENDER_EMAIL'] = ''

        with patch.dict(os.environ, env_patch):
            with pytest.raises(SystemExit):
                load_settings()

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_mailersend_test_mode_workflow(self, mailersend_config):
        """Test MailerSend workflow in test mode."""
        with patch.dict(os.environ, mailersend_config):
            from config.settings import load_settings

            # Test mode requires test recipient email
            settings = load_settings(test_mode=True)

            assert settings.test_recipient_email == "test@example.com"
            assert settings.sender_email == "test@honestpharmco.com"
            assert settings.mailersend_api_token == "test-mailersend-token"

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_mailersend_batch_processing(self, mailersend_config):
        """Test MailerSend batch processing workflow."""
        with patch.dict(os.environ, mailersend_config):
            from src.email_campaign import send_batch_emails

            contacts = [
                {"email": "test1@example.com", "first_name": "John"},
                {"email": "test2@example.com", "first_name": "Jane"},
                {"email": "test3@example.com", "first_name": "Bob"},
            ]

            with patch('src.email_campaign.send_email') as mock_send_email, \
                 patch('time.sleep'):  # Mock sleep to speed up test

                mock_send_email.return_value = True

                successful_sends, next_index = send_batch_emails(contacts, 0, 2)

                assert successful_sends == 2
                assert next_index == 2
                assert mock_send_email.call_count == 2
                mock_send_email.assert_any_call("test1@example.com", "John")
                mock_send_email.assert_any_call("test2@example.com", "Jane")


class TestMailerSendConfigurationEdgeCases:
    """Test edge cases and error conditions for MailerSend configuration."""

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_empty_environment_variables(self):
        """Test behavior with empty environment variables."""
        # Explicitly set required fields to empty to trigger validation
        empty_config = {
            'TIERII_SENDER_EMAIL': '',
            'TIERII_MAILERSEND_API_TOKEN': ''
        }
        with patch.dict(os.environ, empty_config):
            from config.settings import load_settings

            with pytest.raises(SystemExit):
                load_settings()

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_invalid_batch_size_configuration(self):
        """Test handling of invalid batch size configuration."""
        config = {
            'TIERII_SENDER_EMAIL': 'test@example.com',
            'TIERII_MAILERSEND_API_TOKEN': 'test-token',
            'TIERII_CAMPAIGN_BATCH_SIZE': '0'  # Invalid batch size
        }

        with patch.dict(os.environ, config):
            from config.settings import load_settings

            with pytest.raises(SystemExit):  # Should fail validation
                load_settings()

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_invalid_delay_configuration(self):
        """Test handling of invalid delay configuration."""
        config = {
            'TIERII_SENDER_EMAIL': 'test@example.com',
            'TIERII_MAILERSEND_API_TOKEN': 'test-token',
            'TIERII_CAMPAIGN_DELAY_MINUTES': '-1'  # Invalid delay
        }

        with patch.dict(os.environ, config):
            from src.config.settings import load_settings

            with pytest.raises(SystemExit):  # Should fail validation
                load_settings()

    @pytest.mark.integration
    @pytest.mark.mailersend
    def test_sender_name_derivation(self):
        """Test automatic sender name derivation from email."""
        config = {
            'TIERII_SENDER_EMAIL': 'john.doe@example.com',
            'TIERII_MAILERSEND_API_TOKEN': 'test-token'
            # No TIERII_SENDER_NAME provided
        }

        with patch.dict(os.environ, config):
            from src.config.settings import load_settings

            settings = load_settings()

            # Should derive sender name from email
            assert settings.sender_name == "John Doe"  # Derived from john.doe@example.com
