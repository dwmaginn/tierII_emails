"""Integration tests for email_campaign.py full workflow with AuthenticationFactory.

Tests the complete email campaign workflow with different authentication providers,
including configuration loading, authentication, and email sending.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

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


class TestEmailCampaignFullWorkflow:
    """Integration tests for complete email campaign workflow."""

    @pytest.fixture
    def mock_config_mailersend(self):
        """Mock configuration for MailerSend."""
        return {
            "mailersend_api_token": "test_api_token",
            "sender_email": "test@company.com",
            "sender_name": "Test Sender"
        }

    @pytest.fixture
    def mock_contacts_csv(self, tmp_path):
        """Create a temporary CSV file with test contacts."""
        csv_file = tmp_path / "test_contacts.csv"
        csv_content = "Email,Primary Contact Name\ntest1@example.com,John Doe\ntest2@example.com,Jane Smith\n"
        csv_file.write_text(csv_content)
        return str(csv_file)

    @pytest.mark.integration
    @pytest.mark.email
    @patch("email_campaign.auth_manager")
    @patch("email_campaign.create_authentication_manager")
    @patch("email_campaign.send_email")
    @patch("email_campaign.read_contacts_from_csv")
    @patch("builtins.input")
    def test_full_workflow_mailersend_dry_run(self, mock_input, mock_read_contacts, mock_send_email, mock_create_auth, mock_auth_manager):
        """Test full workflow with MailerSend in dry run mode."""
        from email_campaign import main

        # Setup authentication manager
        mock_manager = Mock()
        mock_manager.provider.name = "MAILERSEND"
        mock_auth_factory = Mock()
        mock_auth_factory.get_current_manager.return_value = mock_manager
        mock_create_auth.return_value = mock_auth_factory
        # The mock_auth_manager is already patched, just need to ensure it's not None

        # Setup contacts
        mock_read_contacts.return_value = [
            {"email": "test1@example.com", "first_name": "John", "contact_name": "John Doe"},
            {"email": "test2@example.com", "first_name": "Jane", "contact_name": "Jane Smith"}
        ]

        # Setup send_email to succeed
        mock_send_email.return_value = True

        # Setup user input for dry run
        mock_input.side_effect = ["y", "n"]  # Yes to test email, No to full campaign

        # Run main function
        with patch("sys.argv", ["email_campaign.py", "--dry-run"]):
            main()

        # Verify test email was sent
        mock_send_email.assert_called()
        assert mock_send_email.call_count >= 1

    @pytest.mark.integration
    @pytest.mark.email
    @patch("email_campaign.auth_manager")
    @patch("email_campaign.create_authentication_manager")
    @patch("email_campaign.send_email")
    @patch("email_campaign.read_contacts_from_csv")
    @patch("email_campaign.settings")
    @patch("builtins.input")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_full_workflow_mailersend_full_campaign(self, mock_sleep, mock_input, mock_settings, mock_read_contacts, mock_send_email, mock_create_auth, mock_auth_manager):
        """Test full workflow with MailerSend for full campaign."""
        from email_campaign import main

        # Setup settings with test recipient email
        mock_settings.test_recipient_email = "test@example.com"
        mock_settings.test_fallback_first_name = "Test"
        mock_settings.test_csv_filename = "test.csv"

        # Setup authentication manager
        mock_manager = Mock()
        mock_manager.provider.name = "MAILERSEND"
        mock_auth_factory = Mock()
        mock_auth_factory.get_current_manager.return_value = mock_manager
        mock_create_auth.return_value = mock_auth_factory

        # Setup contacts
        mock_read_contacts.return_value = [
            {"email": "test1@example.com", "first_name": "John", "contact_name": "John Doe"},
            {"email": "test2@example.com", "first_name": "Jane", "contact_name": "Jane Smith"}
        ]

        # Setup send_email to succeed
        mock_send_email.return_value = True

        # Setup user input for full campaign
        mock_input.side_effect = ["y", "y"]  # Yes to test email, Yes to full campaign

        # Run main function
        main()

        # Verify all emails were sent (test + 2 contacts)
        assert mock_send_email.call_count == 3

    @pytest.mark.integration
    @pytest.mark.email
    @patch("email_campaign.auth_manager", None)
    @patch("email_campaign.send_email")
    @patch("email_campaign.read_contacts_from_csv")
    @patch("builtins.input")
    def test_full_workflow_authentication_failure(self, mock_input, mock_read_contacts, mock_send_email):
        """Test full workflow when authentication fails."""
        from email_campaign import main

        # Setup contacts
        mock_read_contacts.return_value = [
            {"email": "test1@example.com", "first_name": "John", "contact_name": "John Doe"}
        ]

        # Run main function - should exit gracefully
        with pytest.raises(SystemExit):
            main()

        # Verify no emails were sent
        mock_send_email.assert_not_called()

    @pytest.mark.integration
    @pytest.mark.email
    @patch("email_campaign.auth_manager")
    @patch("email_campaign.create_authentication_manager")
    @patch("email_campaign.send_email")
    @patch("email_campaign.read_contacts_from_csv")
    @patch("builtins.input")
    def test_full_workflow_fallback_mechanism(self, mock_input, mock_read_contacts, mock_send_email, mock_create_auth, mock_auth_manager):
        """Test full workflow with fallback authentication."""
        from email_campaign import main

        # Setup authentication factory with fallback
        mock_primary = Mock()
        mock_primary.provider.name = "MAILERSEND"
        mock_primary.is_authenticated = False
        
        mock_fallback = Mock()
        mock_fallback.provider.name = "MAILERSEND"
        mock_fallback.is_authenticated = True
        
        mock_auth_factory = Mock()
        mock_auth_factory.get_current_manager.return_value = mock_primary
        mock_auth_factory.get_fallback_manager.return_value = mock_fallback
        mock_create_auth.return_value = mock_auth_factory

        # Setup contacts
        mock_read_contacts.return_value = [
            {"email": "test1@example.com", "first_name": "John", "contact_name": "John Doe"}
        ]

        # Setup send_email to succeed with fallback
        mock_send_email.return_value = True

        # Setup user input
        mock_input.side_effect = ["y", "n"]  # Yes to test email, No to full campaign

        # Run main function
        main()

        # Verify test email was sent using fallback
        mock_send_email.assert_called()

    @pytest.mark.integration
    @pytest.mark.email
    @patch("email_campaign.auth_manager")
    @patch("email_campaign.create_authentication_manager")
    @patch("email_campaign.send_email")
    @patch("email_campaign.read_contacts_from_csv")
    @patch("email_campaign.settings")
    @patch("builtins.input")
    def test_full_workflow_partial_send_failure(self, mock_input, mock_settings, mock_read_contacts, mock_send_email, mock_create_auth, mock_auth_manager):
        """Test full workflow when some emails fail to send."""
        from email_campaign import main

        # Setup settings with test recipient email
        mock_settings.test_recipient_email = "test@example.com"
        mock_settings.test_fallback_first_name = "Test"
        mock_settings.test_csv_filename = "test.csv"

        # Setup authentication manager
        mock_manager = Mock()
        mock_manager.provider.name = "MAILERSEND"
        mock_auth_factory = Mock()
        mock_auth_factory.get_current_manager.return_value = mock_manager
        mock_create_auth.return_value = mock_auth_factory

        # Setup contacts
        mock_read_contacts.return_value = [
            {"email": "test1@example.com", "first_name": "John", "contact_name": "John Doe"},
            {"email": "test2@example.com", "first_name": "Jane", "contact_name": "Jane Smith"},
            {"email": "test3@example.com", "first_name": "Bob", "contact_name": "Bob Johnson"}
        ]

        # Setup send_email to succeed for test and first contact, fail for others
        mock_send_email.side_effect = [True, True, False, False]

        # Setup user input
        mock_input.side_effect = ["y", "y"]  # Yes to test email, Yes to full campaign

        # Run main function
        main()

        # Verify all attempts were made (test + 3 contacts)
        assert mock_send_email.call_count == 4

    @pytest.mark.integration
    @pytest.mark.email
    @patch("email_campaign.auth_manager")
    @patch("email_campaign.create_authentication_manager")
    @patch("email_campaign.read_contacts_from_csv")
    def test_full_workflow_csv_read_failure(self, mock_read_contacts, mock_create_auth, mock_auth_manager):
        """Test full workflow when CSV reading fails."""
        from email_campaign import main

        # Setup authentication manager
        mock_manager = Mock()
        mock_auth_factory = Mock()
        mock_auth_factory.get_current_manager.return_value = mock_manager
        mock_create_auth.return_value = mock_auth_factory

        # Setup CSV reading to fail
        mock_read_contacts.side_effect = FileNotFoundError("CSV file not found")

        # Run main function - should handle error gracefully
        with pytest.raises((FileNotFoundError, SystemExit)):
            main()

    @pytest.mark.integration
    @pytest.mark.email
    @patch("email_campaign.auth_manager")
    @patch("email_campaign.create_authentication_manager")
    @patch("email_campaign.send_email")
    @patch("email_campaign.read_contacts_from_csv")
    @patch("email_campaign.settings")
    @patch("builtins.input")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_full_workflow_batch_processing(self, mock_sleep, mock_input, mock_settings, mock_read_contacts, mock_send_email, mock_create_auth, mock_auth_manager):
        """Test full workflow with batch processing and delays."""
        from email_campaign import main

        # Setup settings with test recipient email
        mock_settings.test_recipient_email = "test@example.com"
        mock_settings.test_fallback_first_name = "Test"
        mock_settings.test_csv_filename = "test.csv"

        # Setup authentication manager
        mock_manager = Mock()
        mock_manager.provider.name = "MAILERSEND"
        mock_auth_factory = Mock()
        mock_auth_factory.get_current_manager.return_value = mock_manager
        mock_create_auth.return_value = mock_auth_factory

        # Setup large contact list to test batching
        contacts = [
            {"email": f"test{i}@example.com", "first_name": f"User{i}", "contact_name": f"User{i}"}
            for i in range(15)  # More than batch size (10)
        ]
        mock_read_contacts.return_value = contacts

        # Setup send_email to succeed
        mock_send_email.return_value = True

        # Setup user input
        mock_input.side_effect = ["y", "y"]  # Yes to test email, Yes to full campaign

        # Run main function
        main()

        # Verify all emails were sent (test + 15 contacts)
        assert mock_send_email.call_count == 16
        
        # Verify sleep was called for batch delays
        assert mock_sleep.call_count > 0


class TestEmailCampaignConfigurationIntegration:
    """Integration tests for configuration loading and authentication setup."""

    @pytest.mark.integration
    @pytest.mark.email
    @patch("config.settings.TierIISettings")
    @patch("email_campaign.authentication_factory")
    def test_create_authentication_manager_with_settings(self, mock_auth_factory, mock_settings):
        """Test authentication manager creation with TierIISettings."""
        from email_campaign import create_authentication_manager

        # Setup mock settings
        mock_settings_instance = Mock()
        mock_settings_instance.mailersend_api_token = "test_api_token"
        mock_settings_instance.sender_email = "test@company.com"
        mock_settings.return_value = mock_settings_instance

        # Setup mock factory
        mock_factory_instance = Mock()
        mock_auth_factory.create_manager.return_value = mock_factory_instance

        # Test
        result = create_authentication_manager()

        # Verify factory was called with MailerSend provider
        mock_auth_factory.create_manager.assert_called_once()
        call_args = mock_auth_factory.create_manager.call_args
        assert call_args[1]['provider'] == AuthenticationProvider.MAILERSEND
        assert result == mock_factory_instance

    @pytest.mark.integration
    @pytest.mark.email
    @patch("config.settings.TierIISettings")
    @patch("email_campaign.authentication_factory")
    def test_create_authentication_manager_settings_fallback(self, mock_auth_factory, mock_settings):
        """Test authentication manager creation with settings import failure."""
        from email_campaign import create_authentication_manager

        # Setup settings import to fail
        mock_settings.side_effect = ImportError("Settings not found")

        # Setup mock factory
        mock_factory_instance = Mock()
        mock_auth_factory.create_manager.return_value = mock_factory_instance

        # Test
        result = create_authentication_manager()

        # Verify factory was called with MailerSend provider
        mock_auth_factory.create_manager.assert_called_once()
        call_args = mock_auth_factory.create_manager.call_args
        assert call_args[1]['provider'] == AuthenticationProvider.MAILERSEND
        assert result == mock_factory_instance

    @pytest.mark.integration
    @pytest.mark.email
    @patch("email_campaign.authentication_factory")
    def test_create_authentication_manager_factory_failure(self, mock_auth_factory):
        """Test authentication manager creation when factory creation fails."""
        from email_campaign import create_authentication_manager

        # Setup factory to fail
        mock_auth_factory.create_manager.side_effect = Exception("Factory creation failed")

        # Test should raise exception
        with pytest.raises(Exception, match="Factory creation failed"):
            create_authentication_manager()

    @pytest.mark.integration
    @pytest.mark.email
    @patch("src.config.settings.TierIISettings")
    @patch("email_campaign.authentication_factory")
    def test_create_authentication_manager_missing_credentials(self, mock_auth_factory, mock_settings):
        """Test authentication manager creation with missing credentials."""
        from email_campaign import create_authentication_manager

        # Setup mock settings with missing credentials
        mock_settings_instance = Mock()
        mock_settings_instance.mailersend_api_token = None
        mock_settings_instance.sender_email = None
        mock_settings.return_value = mock_settings_instance

        # Setup mock factory to raise authentication error
        mock_auth_factory.create_manager.side_effect = AuthenticationError(
            "Missing credentials", 
            AuthenticationProvider.MAILERSEND
        )

        # Test should raise AuthenticationError
        with pytest.raises(AuthenticationError, match="Missing credentials"):
            create_authentication_manager()