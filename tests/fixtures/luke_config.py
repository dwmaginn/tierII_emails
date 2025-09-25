"""Test fixture for Luke's MailerSend configuration.

This fixture provides a complete configuration setup for testing Luke's
MailerSend email workflow with test data.
"""

import os
from typing import Dict, Any


def get_luke_config() -> Dict[str, Any]:
    """Get Luke's MailerSend configuration for testing.

    Returns:
        Dict containing all environment variables for Luke's setup
        with testdata.csv as the recipient source.
    """
    return {
        # Core Email Configuration
        "TIERII_SENDER_EMAIL": "edwards.lukec@gmail.com",
        # MailerSend Configuration
        "TIERII_MAILERSEND_API_TOKEN": "test-api-token-luke",
        "TIERII_SENDER_NAME": "Luke from AI Auto Coach",
        # Campaign Configuration
        "TIERII_CAMPAIGN_BATCH_SIZE": "10",
        "TIERII_CAMPAIGN_DELAY_MINUTES": "1",
        # Test Configuration
        "TIERII_TEST_RECIPIENT_EMAIL": "test@example.com",
        "TIERII_TEST_CSV_FILENAME": "data/test/testdata.csv",
        "TIERII_TEST_FALLBACK_FIRST_NAME": "Friend",
    }


def apply_luke_config() -> None:
    """Apply Luke's configuration to environment variables.

    This function sets all environment variables needed for Luke's
    MailerSend setup during testing.
    """
    config = get_luke_config()
    for key, value in config.items():
        os.environ[key] = str(value)


def clear_luke_config() -> None:
    """Clear Luke's configuration from environment variables.

    This function removes all Luke-specific environment variables
    to ensure clean test isolation.
    """
    config_keys = get_luke_config().keys()
    for key in config_keys:
        os.environ.pop(key, None)
