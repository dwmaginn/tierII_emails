"""
Configuration module for TierII Email System.

This module provides environment-based configuration loading with validation,
default values, and graceful error handling as defined in ST3-002.

Environment Variables:
- TIERII_SENDER_EMAIL: Email address for sending emails (required)
- TIERII_MAILERSEND_API_TOKEN: MailerSend API token (required)
- TIERII_SENDER_NAME: Display name for sender (default: derived from email)
- TIERII_CAMPAIGN_BATCH_SIZE: Batch size for campaigns (default: 50)
- TIERII_CAMPAIGN_DELAY_MINUTES: Delay between batches (default: 5)
- TIERII_EMAIL_TEMPLATE_PATH: Path to email templates (default: None)
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
    validation, and default values for MailerSend-only system.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Core MailerSend configuration
    sender_email: str = Field(..., alias="TIERII_SENDER_EMAIL")
    mailersend_api_token: str = Field(..., alias="TIERII_MAILERSEND_API_TOKEN")
    sender_name: Optional[str] = Field(None, alias="TIERII_SENDER_NAME")

    @field_validator("sender_email", "mailersend_api_token", mode="before")
    @classmethod
    def validate_required_fields(cls, v):
        """Ensure required fields are not empty strings."""
        if v is None or (isinstance(v, str) and v.strip() == ""):
            raise ValueError("Field cannot be empty")
        return v

    # Email template configuration
    email_template_path: Optional[str] = Field(None, alias="TIERII_EMAIL_TEMPLATE_PATH")

    # Campaign configuration
    campaign_batch_size: int = Field(50, alias="TIERII_CAMPAIGN_BATCH_SIZE")
    campaign_delay_minutes: int = Field(5, alias="TIERII_CAMPAIGN_DELAY_MINUTES")

    # Test configuration
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

    @field_validator("sender_name", mode="before")
    @classmethod
    def set_default_sender_name(cls, v, info):
        """Set default sender name from email if not provided."""
        if v is None and info.data and "sender_email" in info.data:
            sender_email = info.data["sender_email"]
            if sender_email and "@" in sender_email:
                # Extract name part before @ and capitalize
                name_part = sender_email.split("@")[0]
                return name_part.replace(".", " ").replace("_", " ").title()
        return v

    @field_validator("campaign_batch_size")
    @classmethod
    def validate_batch_size(cls, v):
        """Validate campaign batch size is reasonable."""
        if v < 1:
            raise ValueError("Campaign batch size must be at least 1")
        if v > 1000:
            logger.warning(
                f"Large batch size ({v}) may cause rate limiting or performance issues"
            )
        return v

    @field_validator("campaign_delay_minutes")
    @classmethod
    def validate_delay_minutes(cls, v):
        """Validate campaign delay is reasonable."""
        if v < 0:
            raise ValueError("Campaign delay cannot be negative")
        if v > 60:
            logger.warning(
                f"Long delay ({v} minutes) may significantly slow down campaigns"
            )
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
        logger.info(f"MailerSend API configured for sender: {settings.sender_name} <{settings.sender_email}>")
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
        logger.error("  TIERII_MAILERSEND_API_TOKEN - MailerSend API token")

        if test_mode:
            logger.error("  TIERII_TEST_RECIPIENT_EMAIL - Test recipient email")

        logger.error("\nOptional environment variables:")
        logger.error("  TIERII_SENDER_NAME - Display name for sender")
        logger.error("  TIERII_EMAIL_TEMPLATE_PATH - Path to email template file")
        logger.error("  TIERII_CAMPAIGN_BATCH_SIZE - Batch size (default: 50)")
        logger.error("  TIERII_CAMPAIGN_DELAY_MINUTES - Delay between batches (default: 5)")

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


# Testing context detection
import inspect


def _is_testing_context():
    """Check if we're running in a testing context."""
    # Check if pytest is in sys.modules (most reliable)
    if 'pytest' in sys.modules:
        return True
    
    # Check call stack for test-related files
    try:
        frame = inspect.currentframe()
        while frame:
            filename = frame.f_code.co_filename
            if "pytest" in filename or "test_" in filename or filename.endswith("conftest.py"):
                return True
            frame = frame.f_back
        return False
    except Exception:
        return False
    finally:
        # Clean up frame reference to prevent memory leaks
        del frame
