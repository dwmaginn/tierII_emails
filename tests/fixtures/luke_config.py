"""Test fixture for Luke's Gmail SMTP configuration.

This fixture provides a complete configuration setup for testing Luke's
Gmail SMTP email workflow with test data.
"""

import os
from typing import Dict, Any


def get_luke_config() -> Dict[str, Any]:
    """Get Luke's Gmail SMTP configuration for testing.
    
    Returns:
        Dict containing all environment variables for Luke's setup
        with testdata.csv as the recipient source.
    """
    return {
        # Core Email Configuration
        "TIERII_SENDER_EMAIL": "luke@aiautocoach.com",
        "TIERII_SMTP_SERVER": "smtp.gmail.com",
        "TIERII_SMTP_PORT": "587",
        
        # Authentication Configuration
        "TIERII_AUTH_PROVIDER": "gmail",
        
        # Gmail Authentication Configuration
        "TIERII_GMAIL_USERNAME": "luke@aiautocoach.com",
        "TIERII_GMAIL_APP_PASSWORD": "test-app-password-luke",
        
        # Email Content Configuration
        "TIERII_EMAIL_SUBJECT": "Cannabis Business Opportunity - AI Auto Coach",
        "TIERII_SMTP_SENDER_NAME": "Luke from AI Auto Coach",
        
        # Test-specific Configuration
        "TIERII_TEST_RECIPIENT_EMAIL": "test@example.com",
        "TIERII_CSV_FILE_PATH": "c:/Users/73spi/Work/tierII_emails/data/test/testdata.csv",
        
        # Optional Configuration
        "TIERII_BATCH_SIZE": "10",
        "TIERII_DELAY_MINUTES": "1",
        "TIERII_DRY_RUN": "true",  # Prevent actual email sending in tests
    }


def apply_luke_config() -> None:
    """Apply Luke's configuration to environment variables.
    
    This function sets all environment variables needed for Luke's
    Gmail SMTP setup during testing.
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