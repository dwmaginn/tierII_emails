"""Integration tests for configuration-specific email workflows.

These tests verify that the full email workflow functions correctly
with different user configurations (David's Microsoft OAuth and Luke's Gmail SMTP)
while using test data to prevent unintended email sends.
"""

import pytest
from unittest.mock import patch

from tests.fixtures import (
    get_david_config,
    apply_david_config,
    clear_david_config,
    get_luke_config,
    apply_luke_config,
    clear_luke_config,
)


class TestDavidMicrosoftWorkflow:
    """Test David's Microsoft OAuth email workflow."""

    def setup_method(self):
        """Set up David's configuration before each test."""
        apply_david_config()

    def teardown_method(self):
        """Clean up David's configuration after each test."""
        clear_david_config()

    @pytest.mark.integration
    @pytest.mark.oauth
    def test_david_config_loading(self):
        """Test that David's configuration loads correctly."""
        from src.config.settings import load_settings

        settings = load_settings()

        # Verify core email settings
        assert settings.sender_email == "david@honestpharmco.com"
        assert settings.smtp_server == "smtp.office365.com"
        assert settings.smtp_port == 587

        # Verify authentication provider
        assert settings.auth_provider == "microsoft"

        # Verify Microsoft OAuth settings
        assert settings.tenant_id == "test-tenant-id-david"
        assert settings.client_id == "test-client-id-david"
        assert settings.client_secret == "test-client-secret-david"

        # Verify email content
        assert "Honest Pharmco" in settings.email_subject
        assert "David" in settings.smtp_sender_name

    @pytest.mark.integration
    @pytest.mark.oauth
    def test_david_csv_data_loading(self):
        """Test that David's configuration uses testdata.csv."""
        from src.utils.csv_reader import load_contacts

        # Load contacts using David's configuration
        contacts = load_contacts()

        # Verify we're using test data
        assert len(contacts) == 3  # testdata.csv has 3 records

        # Verify test email addresses are present
        test_emails = [contact["Email"] for contact in contacts]
        assert "edwards.lukec@gmail.com" in test_emails
        assert "73spider73@gmail.com" in test_emails
        assert "lce1868@rit.edu" in test_emails

    @pytest.mark.integration
    @pytest.mark.oauth
    @patch("src.auth.oauth_manager.OAuthManager.get_access_token")
    @patch("src.email.smtp_client.SMTPClient.send_email")
    def test_david_full_workflow_dry_run(self, mock_send_email, mock_get_token):
        """Test David's full email workflow in dry run mode."""
        # Mock OAuth token response
        mock_get_token.return_value = "mock-access-token"

        # Mock email sending (should not be called in dry run)
        mock_send_email.return_value = True

        from src.email_campaign import EmailCampaign

        campaign = EmailCampaign()
        result = campaign.run_campaign()

        # Verify dry run behavior
        assert result is not None
        # In dry run mode, emails should not actually be sent
        mock_send_email.assert_not_called()


class TestLukeGmailWorkflow:
    """Test Luke's Gmail SMTP email workflow."""

    def setup_method(self):
        """Set up Luke's configuration before each test."""
        apply_luke_config()

    def teardown_method(self):
        """Clean up Luke's configuration after each test."""
        clear_luke_config()

    @pytest.mark.integration
    @pytest.mark.email
    def test_luke_config_loading(self):
        """Test that Luke's configuration loads correctly."""
        from src.config.settings import load_settings

        settings = load_settings()

        # Verify core email settings
        assert settings.sender_email == "edwards.lukec@gmail.com"
        assert settings.smtp_server == "smtp.gmail.com"
        assert settings.smtp_port == 587

        # Verify authentication provider
        assert settings.auth_provider == "gmail"

        # Verify Gmail settings
        assert settings.gmail_username == "edwards.lukec@gmail.com"
        assert settings.gmail_app_password == "test-app-password-luke"

        # Verify email content
        assert "AI Auto Coach" in settings.email_subject
        assert "Luke" in settings.smtp_sender_name

    @pytest.mark.integration
    @pytest.mark.email
    def test_luke_csv_data_loading(self):
        """Test that Luke's configuration uses testdata.csv."""
        from src.utils.csv_reader import load_contacts

        # Load contacts using Luke's configuration
        contacts = load_contacts()

        # Verify we're using test data
        assert len(contacts) == 3  # testdata.csv has 3 records

        # Verify test email addresses are present
        test_emails = [contact["Email"] for contact in contacts]
        assert "edwards.lukec@gmail.com" in test_emails
        assert "73spider73@gmail.com" in test_emails
        assert "lce1868@rit.edu" in test_emails

    @pytest.mark.integration
    @pytest.mark.email
    @patch("src.email.smtp_client.SMTPClient.send_email")
    def test_luke_full_workflow_dry_run(self, mock_send_email):
        """Test Luke's full email workflow in dry run mode."""
        # Mock email sending (should not be called in dry run)
        mock_send_email.return_value = True

        from src.email_campaign import EmailCampaign

        campaign = EmailCampaign()
        result = campaign.run_campaign()

        # Verify dry run behavior
        assert result is not None
        # In dry run mode, emails should not actually be sent
        mock_send_email.assert_not_called()


class TestConfigurationIsolation:
    """Test that configurations are properly isolated between tests."""

    @pytest.mark.integration
    def test_config_isolation_david_to_luke(self):
        """Test switching from David's config to Luke's config."""
        # Apply David's config
        apply_david_config()

        from src.config.settings import load_settings

        david_settings = load_settings()
        assert david_settings.auth_provider == "microsoft"
        assert "david@honestpharmco.com" == david_settings.sender_email

        # Clear David's config and apply Luke's
        clear_david_config()
        apply_luke_config()

        # Reload settings to get Luke's config
        luke_settings = load_settings()
        assert luke_settings.auth_provider == "gmail"
        assert "edwards.lukec@gmail.com" == luke_settings.sender_email

        # Clean up
        clear_luke_config()

    @pytest.mark.integration
    def test_config_isolation_luke_to_david(self):
        """Test switching from Luke's config to David's config."""
        # Apply Luke's config
        apply_luke_config()

        from src.config.settings import load_settings

        luke_settings = load_settings()
        assert luke_settings.auth_provider == "gmail"
        assert "edwards.lukec@gmail.com" == luke_settings.sender_email

        # Clear Luke's config and apply David's
        clear_luke_config()
        apply_david_config()

        # Reload settings to get David's config
        david_settings = load_settings()
        assert david_settings.auth_provider == "microsoft"
        assert "david@honestpharmco.com" == david_settings.sender_email

        # Clean up
        clear_david_config()


class TestTestDataSafety:
    """Test that configurations properly use test data to prevent unintended emails."""

    @pytest.mark.integration
    def test_david_uses_test_data_path(self):
        """Test that David's config points to testdata.csv."""
        apply_david_config()

        config = get_david_config()
        csv_path = config.get("TIERII_CSV_FILE_PATH")

        assert csv_path is not None
        assert "testdata.csv" in csv_path
        assert "test" in csv_path.lower()

        clear_david_config()

    @pytest.mark.integration
    def test_luke_uses_test_data_path(self):
        """Test that Luke's config points to testdata.csv."""
        apply_luke_config()

        config = get_luke_config()
        csv_path = config.get("TIERII_CSV_FILE_PATH")

        assert csv_path is not None
        assert "testdata.csv" in csv_path
        assert "test" in csv_path.lower()

        clear_luke_config()

    @pytest.mark.integration
    def test_dry_run_enabled_by_default(self):
        """Test that dry run is enabled by default in test fixtures."""
        # Test David's config
        david_config = get_david_config()
        assert david_config.get("TIERII_DRY_RUN") == "true"

        # Test Luke's config
        luke_config = get_luke_config()
        assert luke_config.get("TIERII_DRY_RUN") == "true"
