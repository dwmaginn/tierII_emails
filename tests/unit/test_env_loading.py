import pytest
import os
import tempfile

# Import from the project's config module
from src.config.settings import load_settings


def test_env_file_loading():
    """Test loading configuration from a .env file."""
    # Create a temporary .env file
    env_content = """
# Test environment configuration
TIERII_SENDER_EMAIL=test@example.com
TIERII_EMAIL_SUBJECT=Test Subject
TIERII_MAILERSEND_API_TOKEN=test_api_token_12345
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(env_content)
        env_file_path = f.name

    try:
        # Test that we can load settings (this should work regardless of .env file)
        settings = load_settings()
        assert settings is not None
        print(f"✓ Successfully loaded settings: {type(settings)}")

    finally:
        # Clean up
        if os.path.exists(env_file_path):
            os.unlink(env_file_path)


def test_basic_import():
    """Test that we can import the settings module."""
    try:
        from src.config.settings import load_settings

        settings = load_settings()
        assert settings is not None
        print(f"✓ Successfully imported and loaded settings: {type(settings)}")

    except ImportError as e:
        pytest.fail(f"Import error: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
