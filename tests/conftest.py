"""Shared pytest fixtures and configurations for email campaign tests."""

import pytest
from unittest.mock import Mock, MagicMock
import tempfile
import os
from freezegun import freeze_time


# Mock configuration data
@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "SENDER_EMAIL": "test@example.com",
        "SMTP_SERVER": "smtp.office365.com",
        "SMTP_PORT": 587,
        "TENANT_ID": "test-tenant-id",
        "CLIENT_ID": "test-client-id",
        "CLIENT_SECRET": "test-client-secret",
        "BATCH_SIZE": 5,
        "DELAY_MINUTES": 1,
    }


# Mock OAuth responses
@pytest.fixture
def mock_oauth_response():
    """Mock OAuth token response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "test-access-token-12345",
        "token_type": "Bearer",
        "expires_in": 3600,
    }
    return mock_response


@pytest.fixture
def mock_successful_response():
    """Mock successful OAuth response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "test-access-token-12345",
        "token_type": "Bearer",
        "expires_in": 3600,
    }
    return mock_response


@pytest.fixture
def mock_error_response():
    """Mock error OAuth response."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error": "invalid_client",
        "error_description": "Invalid client credentials",
    }
    return mock_response


# Sample contact data
@pytest.fixture
def sample_contacts():
    """Sample contact data for testing."""
    return [
        {"name": "John Doe", "email": "john.doe@example.com"},
        {"name": "Jane Smith", "email": "jane.smith@example.com"},
        {"name": "Bob Johnson", "email": "bob.johnson@example.com"},
        {"name": "Alice Brown", "email": "alice.brown@example.com"},
        {"name": "Charlie Wilson", "email": "charlie.wilson@example.com"},
    ]


@pytest.fixture
def sample_csv_data():
    """Sample CSV data as string."""
    return """name,email
John Doe,john.doe@example.com
Jane Smith,jane.smith@example.com
Bob Johnson,bob.johnson@example.com
Alice Brown,alice.brown@example.com
Charlie Wilson,charlie.wilson@example.com
"""


@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(sample_csv_data)
        temp_file_path = f.name

    yield temp_file_path

    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


# Mock SMTP server
@pytest.fixture
def mock_smtp_server():
    """Mock SMTP server for testing email sending."""
    mock_server = MagicMock()
    mock_server.starttls.return_value = None
    mock_server.auth.return_value = None
    mock_server.send_message.return_value = {}
    mock_server.quit.return_value = None
    return mock_server


# Mock requests.post
@pytest.fixture
def mock_requests_post():
    """Mock requests.post for OAuth testing."""
    return Mock()


# Patch config import
@pytest.fixture(autouse=True)
def patch_config_import(monkeypatch, mock_config):
    """Patch config imports for testing."""
    import sys

    # Mock the config module
    mock_config_module = Mock()
    for key, value in mock_config.items():
        setattr(mock_config_module, key, value)

    # Patch the config module in sys.modules before import
    monkeypatch.setitem(sys.modules, "config", mock_config_module)
    return mock_config_module


# Freeze time fixture
@pytest.fixture
def freeze_time_fixture():
    """Fixture to freeze time for testing."""
    with freeze_time("2024-01-01 12:00:00") as frozen_time:
        yield frozen_time


# OAuth token manager fixture
@pytest.fixture
def oauth_token_manager():
    """Create an OAuthTokenManager instance for testing."""
    from src.email_campaign import OAuthTokenManager

    return OAuthTokenManager()


# Configuration workflow fixtures
@pytest.fixture
def david_config_fixture():
    """Fixture that applies David's configuration for the test duration."""
    from tests.fixtures import apply_david_config, clear_david_config

    apply_david_config()
    yield
    clear_david_config()


@pytest.fixture
def luke_config_fixture():
    """Fixture that applies Luke's configuration for the test duration."""
    from tests.fixtures import apply_luke_config, clear_luke_config

    apply_luke_config()
    yield
    clear_luke_config()


@pytest.fixture
def isolated_config():
    """Fixture that ensures clean environment isolation between tests."""
    # Store original environment
    original_env = dict(os.environ)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def token_manager():
    """Alias for oauth_token_manager for backward compatibility."""
    from src.email_campaign import OAuthTokenManager

    return OAuthTokenManager()
