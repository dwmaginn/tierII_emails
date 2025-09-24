"""Test fixture for David's MailerSend configuration.

This fixture provides a complete configuration setup for testing David's
MailerSend email workflow with test data.
"""

import os
from typing import Dict, Any


def get_david_config() -> Dict[str, Any]:
    """Get David's MailerSend configuration for testing.

    Returns:
        Dict containing all environment variables for David's setup
        with testdata.csv as the recipient source.
    """
    return {
        # Core Email Configuration
        "TIERII_SENDER_EMAIL": "david@honestpharmco.com",
        # MailerSend Configuration
        "TIERII_MAILERSEND_API_TOKEN": "test-api-token-david",
        "TIERII_SENDER_NAME": "David from Honest Pharmco",
        # Campaign Configuration
        "TIERII_CAMPAIGN_BATCH_SIZE": "10",
        "TIERII_CAMPAIGN_DELAY_MINUTES": "1",
        # Test Configuration
        "TIERII_TEST_RECIPIENT_EMAIL": "test@example.com",
        "TIERII_TEST_CSV_FILENAME": "data/test/testdata.csv",
        "TIERII_TEST_FALLBACK_FIRST_NAME": "Friend",
    }


def apply_david_config() -> None:
    """Apply David's configuration to environment variables.

    This function sets all environment variables needed for David's
    MailerSend setup during testing.
    """
    config = get_david_config()
    for key, value in config.items():
        os.environ[key] = str(value)


def clear_david_config() -> None:
    """Clear David's configuration from environment variables.

    This function removes all David-specific environment variables
    to ensure clean test isolation.
    """
    config_keys = get_david_config().keys()
    for key in config_keys:
        os.environ.pop(key, None)
