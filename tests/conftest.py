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
        "MAILERSEND_API_TOKEN": "test-api-token-12345",
        "BATCH_SIZE": 5,
        "DELAY_MINUTES": 1,
    }


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


# Patch config import
@pytest.fixture
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


# Configuration workflow fixtures
@pytest.fixture
def david_config_fixture():
    """Fixture that applies David's MailerSend configuration for the test duration."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from tests.fixtures import apply_david_config, clear_david_config

    apply_david_config()
    yield
    clear_david_config()


@pytest.fixture
def luke_config_fixture():
    """Fixture that applies Luke's MailerSend configuration for the test duration."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
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
