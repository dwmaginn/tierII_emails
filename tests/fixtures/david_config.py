"""Test fixture for David's Microsoft OAuth configuration.

This fixture provides a complete configuration setup for testing David's
Microsoft 365 OAuth 2.0 email workflow with test data.
"""

import os
from typing import Dict, Any


def get_david_config() -> Dict[str, Any]:
    """Get David's Microsoft OAuth configuration for testing.
    
    Returns:
        Dict containing all environment variables for David's setup
        with testdata.csv as the recipient source.
    """
    return {
        # Core Email Configuration
        "TIERII_SENDER_EMAIL": "david@honestpharmco.com",
        "TIERII_SMTP_SERVER": "smtp.office365.com",
        "TIERII_SMTP_PORT": "587",
        
        # Authentication Configuration
        "TIERII_AUTH_PROVIDER": "microsoft",
        
        # Microsoft OAuth 2.0 Configuration
        "TIERII_TENANT_ID": "test-tenant-id-david",
        "TIERII_CLIENT_ID": "test-client-id-david",
        "TIERII_CLIENT_SECRET": "test-client-secret-david",
        
        # Email Content Configuration
        "TIERII_EMAIL_SUBJECT": "High-Quality Cannabis Available - Honest Pharmco",
        "TIERII_SMTP_SENDER_NAME": "David from Honest Pharmco",
        
        # Test-specific Configuration
        "TIERII_TEST_RECIPIENT_EMAIL": "test@example.com",
        "TIERII_CSV_FILE_PATH": "c:/Users/73spi/Work/tierII_emails/data/test/testdata.csv",
        
        # Optional Configuration
        "TIERII_BATCH_SIZE": "10",
        "TIERII_DELAY_MINUTES": "1",
        "TIERII_DRY_RUN": "true",  # Prevent actual email sending in tests
    }


def apply_david_config() -> None:
    """Apply David's configuration to environment variables.
    
    This function sets all environment variables needed for David's
    Microsoft OAuth setup during testing.
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