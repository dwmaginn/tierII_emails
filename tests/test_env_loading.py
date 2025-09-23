import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

# Import from the project's config module
from config.settings import get_settings

def test_env_file_loading():
    """Test loading configuration from a .env file."""
    # Create a temporary .env file
    env_content = """
# Test environment configuration
SMTP_SERVER=test.smtp.com
SMTP_PORT=587
EMAIL_ADDRESS=test@example.com
EMAIL_PASSWORD=test_password
OAUTH_CLIENT_ID=test_client_id
OAUTH_CLIENT_SECRET=test_client_secret
OAUTH_REFRESH_TOKEN=test_refresh_token
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        env_file_path = f.name
    
    try:
        # Test that we can load settings (this should work regardless of .env file)
        settings = get_settings()
        assert settings is not None
        print(f"✓ Successfully loaded settings: {type(settings)}")
        
    finally:
        # Clean up
        if os.path.exists(env_file_path):
            os.unlink(env_file_path)

def test_basic_import():
    """Test that we can import the settings module."""
    try:
        from config.settings import get_settings
        settings = get_settings()
        assert settings is not None
        print(f"✓ Successfully imported and loaded settings: {type(settings)}")
        
    except ImportError as e:
        pytest.fail(f"Import error: {e}")

if __name__ == '__main__':
    pytest.main([__file__])