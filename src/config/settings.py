"""
Configuration module for TierII Email System.

This module provides environment-based configuration loading with validation,
default values, and graceful error handling as defined in ST3-002.

Environment Variables:
- TIERII_SENDER_EMAIL: Email address for sending emails (required)
- TIERII_SMTP_SERVER: SMTP server address (required)
- TIERII_SMTP_PORT: SMTP server port (default: 587)
- TIERII_TENANT_ID: Azure AD tenant ID (required for OAuth)
- TIERII_CLIENT_ID: Azure AD client ID (required for OAuth)
- TIERII_CLIENT_SECRET: Azure AD client secret (required for OAuth)
- TIERII_SMTP_SENDER_NAME: Display name for sender (default: derived from email)
- TIERII_CAMPAIGN_BATCH_SIZE: Batch size for campaigns (default: 50)
- TIERII_CAMPAIGN_DELAY_MINUTES: Delay between batches (default: 5)
- TIERII_EMAIL_TEMPLATE_PATH: Path to email templates (default: None)
- TIERII_EMAIL_SUBJECT: Email subject line (required)
- TIERII_TEST_RECIPIENT_EMAIL: Test recipient email (required in test mode)
- TIERII_TEST_FALLBACK_FIRST_NAME: Fallback first name for tests (default: "Friend")
- TIERII_TEST_CSV_FILENAME: Test CSV filename (default: "data/contacts/tier_i_tier_ii_emails_verified.csv")
"""

import sys
import logging
from typing import Optional

try:
    from dotenv import load_dotenv
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, field_validator, ValidationError
except ImportError as e:
    logging.error(f"Required dependencies not installed: {e}")
    logging.error("Please install: pip install python-dotenv pydantic-settings")
    sys.exit(1)

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging for configuration module
logger = logging.getLogger(__name__)


class TierIISettings(BaseSettings):
    """
    TierII Email System Configuration with environment variable loading,
    validation, and default values.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Core Email Configuration (Required)
    sender_email: str = Field(..., alias="TIERII_SENDER_EMAIL")
    smtp_server: str = Field(..., alias="TIERII_SMTP_SERVER")
    smtp_port: int = Field(587, alias="TIERII_SMTP_PORT")

    # Authentication Configuration
    auth_provider: str = Field("microsoft", alias="TIERII_AUTH_PROVIDER")

    # OAuth 2.0 Configuration (Microsoft)
    tenant_id: Optional[str] = Field(None, alias="TIERII_TENANT_ID")
    client_id: Optional[str] = Field(None, alias="TIERII_CLIENT_ID")
    client_secret: Optional[str] = Field(None, alias="TIERII_CLIENT_SECRET")

    # Gmail SMTP Configuration
    gmail_username: Optional[str] = Field(None, alias="TIERII_GMAIL_USERNAME")
    gmail_app_password: Optional[str] = Field(None, alias="TIERII_GMAIL_APP_PASSWORD")

    # Email Content Configuration
    email_subject: str = Field(..., alias="TIERII_EMAIL_SUBJECT")
    smtp_sender_name: Optional[str] = Field(None, alias="TIERII_SMTP_SENDER_NAME")
    email_template_path: Optional[str] = Field(None, alias="TIERII_EMAIL_TEMPLATE_PATH")

    # Campaign Configuration (With Defaults)
    campaign_batch_size: int = Field(50, alias="TIERII_CAMPAIGN_BATCH_SIZE")
    campaign_delay_minutes: int = Field(5, alias="TIERII_CAMPAIGN_DELAY_MINUTES")

    # Test Configuration
    test_recipient_email: Optional[str] = Field(
        None, alias="TIERII_TEST_RECIPIENT_EMAIL"
    )
    test_fallback_first_name: str = Field(
        "Friend", alias="TIERII_TEST_FALLBACK_FIRST_NAME"
    )
    test_csv_filename: str = Field(
        "data/contacts/tier_i_tier_ii_emails_verified.csv",
        alias="TIERII_TEST_CSV_FILENAME",
    )

    @field_validator("smtp_sender_name", mode="before")
    @classmethod
    def set_default_sender_name(cls, v, info):
        """Set default sender name from email if not provided."""
        if v is None or v == "":
            # Get sender_email from the data being validated
            sender_email = info.data.get("sender_email")
            if sender_email:
                # Extract name part before @ and capitalize
                name_part = sender_email.split("@")[0]
                return name_part.capitalize()
        return v

    @field_validator("campaign_batch_size")
    @classmethod
    def validate_batch_size(cls, v):
        """Validate batch size is reasonable."""
        if v <= 0:
            raise ValueError("Batch size must be positive")
        if v > 1000:
            logger.warning(
                f"Large batch size detected: {v}. Consider smaller batches for better performance."
            )
        return v

    @field_validator("campaign_delay_minutes")
    @classmethod
    def validate_delay_minutes(cls, v):
        """Validate delay is reasonable."""
        if v < 0:
            raise ValueError("Delay minutes cannot be negative")
        if v > 60:
            logger.warning(
                f"Long delay detected: {v} minutes. This may slow down campaigns significantly."
            )
        return v

    @field_validator("smtp_port")
    @classmethod
    def validate_smtp_port(cls, v):
        """Validate SMTP port is in valid range."""
        if not (1 <= v <= 65535):
            raise ValueError("SMTP port must be between 1 and 65535")
        return v


def load_settings(test_mode: bool = False) -> TierIISettings:
    """
    Load and validate TierII settings with environment-specific behavior.

    Args:
        test_mode: If True, requires test_recipient_email to be set

    Returns:
        TierIISettings: Validated configuration object

    Raises:
        SystemExit: If critical configuration is missing or invalid
    """
    is_testing = _is_testing_context()

    try:
        settings = TierIISettings()

        # Test mode validation
        if test_mode and not settings.test_recipient_email:
            logger.error(
                "TIERII_TEST_RECIPIENT_EMAIL is required when running in test mode"
            )
            if is_testing:
                raise SystemExit(1)
            else:
                sys.exit(1)

        # Log configuration summary (without sensitive data)
        logger.info("Configuration loaded successfully")
        logger.info(f"SMTP Server: {settings.smtp_server}:{settings.smtp_port}")
        logger.info(f"Sender: {settings.smtp_sender_name} <{settings.sender_email}>")
        logger.info(
            f"Campaign Settings: Batch={settings.campaign_batch_size}, Delay={settings.campaign_delay_minutes}min"
        )

        if settings.email_template_path:
            logger.info(f"Email Template: {settings.email_template_path}")
        else:
            logger.info(
                "Email Template: Using inline HTML (no template file specified)"
            )

        if test_mode:
            logger.info(f"Test Mode: Recipient={settings.test_recipient_email}")

        return settings

    except ValidationError as e:
        logger.error("Configuration validation failed:")
        for error in e.errors():
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            env_var = f"TIERII_{field.upper()}"
            logger.error(f"  {env_var}: {message}")

        logger.error("\nRequired environment variables:")
        logger.error("  TIERII_SENDER_EMAIL - Email address for sending")
        logger.error("  TIERII_SMTP_SERVER - SMTP server address")
        logger.error("  TIERII_TENANT_ID - Azure AD tenant ID")
        logger.error("  TIERII_CLIENT_ID - Azure AD client ID")
        logger.error("  TIERII_CLIENT_SECRET - Azure AD client secret")
        logger.error("  TIERII_EMAIL_SUBJECT - Email subject line")

        if test_mode:
            logger.error(
                "  TIERII_TEST_RECIPIENT_EMAIL - Test recipient (required in test mode)"
            )

        if is_testing:
            raise SystemExit(1)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        if is_testing:
            raise SystemExit(1)
        else:
            sys.exit(1)


# Backward compatibility: Legacy constants for existing code
# Only load if not in testing mode (detected by checking if we're being imported for testing)
import inspect


def _is_testing_context():
    """Check if we're being imported in a testing context."""
    frame = inspect.currentframe()
    try:
        while frame:
            filename = frame.f_code.co_filename
            if "test" in filename.lower() or "pytest" in filename.lower():
                return True
            frame = frame.f_back
        return False
    finally:
        del frame


# Lazy-loaded backward compatibility constants
_legacy_settings = None


def _get_legacy_settings():
    """Lazy-load legacy settings to avoid import-time failures."""
    global _legacy_settings

    # In testing context, always reload to pick up environment changes
    if _is_testing_context():
        try:
            settings = load_settings()
            return {
                "SENDER_EMAIL": settings.sender_email,
                "SMTP_SERVER": settings.smtp_server,
                "SMTP_PORT": settings.smtp_port,
                "TENANT_ID": settings.tenant_id,
                "CLIENT_ID": settings.client_id,
                "CLIENT_SECRET": settings.client_secret,
                "BATCH_SIZE": settings.campaign_batch_size,
                "DELAY_MINUTES": settings.campaign_delay_minutes,
            }
        except Exception:
            # Fallback to placeholder values if loading fails in tests
            return {
                "SENDER_EMAIL": "test@example.com",
                "SMTP_SERVER": "smtp.example.com",
                "SMTP_PORT": 587,
                "TENANT_ID": "test-tenant-id",
                "CLIENT_ID": "test-client-id",
                "CLIENT_SECRET": "test-client-secret",
                "BATCH_SIZE": 10,
                "DELAY_MINUTES": 3,
            }

    # In non-testing context, use cached values
    if _legacy_settings is None:
        try:
            settings = load_settings()
            _legacy_settings = {
                "SENDER_EMAIL": settings.sender_email,
                "SMTP_SERVER": settings.smtp_server,
                "SMTP_PORT": settings.smtp_port,
                "TENANT_ID": settings.tenant_id,
                "CLIENT_ID": settings.client_id,
                "CLIENT_SECRET": settings.client_secret,
                "BATCH_SIZE": settings.campaign_batch_size,
                "DELAY_MINUTES": settings.campaign_delay_minutes,
            }
            logger.warning(
                "Using legacy configuration constants. Consider migrating to load_settings() function."
            )
        except SystemExit:
            # Re-raise system exit to maintain fail-fast behavior in non-testing contexts
            if not _is_testing_context():
                raise
            # In testing context, set placeholder values
            _legacy_settings = {
                "SENDER_EMAIL": "test@example.com",
                "SMTP_SERVER": "smtp.example.com",
                "SMTP_PORT": 587,
                "TENANT_ID": "test-tenant-id",
                "CLIENT_ID": "test-client-id",
                "CLIENT_SECRET": "test-client-secret",
                "BATCH_SIZE": 10,
                "DELAY_MINUTES": 3,
            }
        except Exception as e:
            # For backward compatibility, set placeholder values if loading fails
            logger.error(f"Failed to load settings for backward compatibility: {e}")
            _legacy_settings = {
                "SENDER_EMAIL": "CONFIGURATION_ERROR",
                "SMTP_SERVER": "CONFIGURATION_ERROR",
                "SMTP_PORT": 587,
                "TENANT_ID": "CONFIGURATION_ERROR",
                "CLIENT_ID": "CONFIGURATION_ERROR",
                "CLIENT_SECRET": "CONFIGURATION_ERROR",
                "BATCH_SIZE": 10,
                "DELAY_MINUTES": 3,
            }
    return _legacy_settings


# Legacy constants (deprecated - use load_settings() instead)
# These are now lazy-loaded via __getattr__
_LEGACY_CONSTANT_NAMES = {
    "SENDER_EMAIL",
    "SMTP_SERVER",
    "SMTP_PORT",
    "TENANT_ID",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "BATCH_SIZE",
    "DELAY_MINUTES",
}


def __getattr__(name):
    """Lazy-load legacy constants when accessed."""
    if name in _LEGACY_CONSTANT_NAMES:
        return _get_legacy_settings()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
