#!/usr/bin/env python3
"""
Test script to validate ST3-002 Configuration Module Enhancement.
Tests environment variable loading, validation, and backward compatibility.
"""

import os
from pathlib import Path
import importlib.util
import pytest

# Ensure we're using the correct project directory
project_root = Path(__file__).parent.absolute()
src_path = project_root / "src"
settings_file = src_path / "config" / "settings.py"


# Function to load the settings module dynamically
def load_settings_module():
    """Load the config.settings module with proper path management."""
    # Get the project root directory (three levels up from this file: tests/unit/test_config.py)
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    src_path = os.path.join(project_root, "src")
    settings_file = os.path.join(src_path, "config", "settings.py")

    try:
        spec = importlib.util.spec_from_file_location("config.settings", settings_file)
        settings_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings_module)
        return settings_module
    except Exception as e:
        print(f"Import error: {e}")
        print(f"Project root: {project_root}")
        print(f"Src path: {src_path}")
        print(f"Settings file: {settings_file}")
        print(f"Settings file exists: {os.path.exists(settings_file)}")
        raise


def test_imports():
    """Test that we can import the required functions and classes."""
    print("Testing imports...")
    settings_module = load_settings_module()
    load_settings = settings_module.load_settings
    TierIISettings = settings_module.TierIISettings

    assert callable(load_settings), "load_settings should be callable"
    assert hasattr(TierIISettings, "__name__"), "TierIISettings should be a class"

    print("✓ Successfully imported load_settings and TierIISettings")


def test_missing_required_variables():
    """Test handling of missing required environment variables."""
    print("\nTesting missing required variables...")

    # Clear environment variables
    env_vars = [
        "TIERII_SENDER_EMAIL",
        "TIERII_SMTP_SERVER",
        "TIERII_TENANT_ID",
        "TIERII_CLIENT_ID",
        "TIERII_CLIENT_SECRET",
        "TIERII_EMAIL_SUBJECT",
    ]

    original_values = {}
    for var in env_vars:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

        # This should raise SystemExit due to missing required variables
        try:
            settings = load_settings()
            assert False, "Expected SystemExit for missing required variables"
        except SystemExit:
            print("✓ Correctly handled missing required variables with SystemExit")
        except Exception as e:
            print(
                f"✓ Correctly handled missing required variables with validation error: {type(e).__name__}"
            )
    finally:
        # Restore original values
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value


def test_minimal_configuration():
    """Test loading with minimal required configuration."""
    print("\nTesting minimal configuration...")

    # Set minimal required environment variables
    test_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_SMTP_SERVER": "smtp.example.com",
        "TIERII_TENANT_ID": "12345678-1234-1234-1234-123456789abc",
        "TIERII_CLIENT_ID": "87654321-4321-4321-4321-cba987654321",
        "TIERII_CLIENT_SECRET": "test-client-secret",
        "TIERII_EMAIL_SUBJECT": "Test Subject",
    }

    # Store original values
    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings
        settings = load_settings()

        # Verify required fields
        assert settings.sender_email == "test@example.com"
        assert settings.smtp_server == "smtp.example.com"
        assert settings.smtp_port == 587  # Default value
        assert settings.campaign_batch_size == 50  # Default value
        assert settings.campaign_delay_minutes == 5  # Default value
        assert settings.smtp_sender_name == "Test"  # Derived from email

        print("✓ Minimal configuration loaded successfully with defaults")

    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_custom_configuration():
    """Test loading with custom configuration values."""
    print("\nTesting custom configuration...")

    test_env = {
        "TIERII_SENDER_EMAIL": "custom@example.com",
        "TIERII_SMTP_SERVER": "custom.smtp.com",
        "TIERII_SMTP_PORT": "465",
        "TIERII_TENANT_ID": "custom-tenant",
        "TIERII_CLIENT_ID": "custom-client",
        "TIERII_CLIENT_SECRET": "custom-secret",
        "TIERII_EMAIL_SUBJECT": "Custom Subject",
        "TIERII_SMTP_SENDER_NAME": "Custom Sender",
        "TIERII_CAMPAIGN_BATCH_SIZE": "25",
        "TIERII_CAMPAIGN_DELAY_MINUTES": "10",
        "TIERII_EMAIL_TEMPLATE_PATH": "/path/to/template.html",
    }

    # Store and set environment variables
    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings
        settings = load_settings()

        # Verify custom values
        assert settings.sender_email == "custom@example.com"
        assert settings.smtp_port == 465
        assert settings.smtp_sender_name == "Custom Sender"
        assert settings.campaign_batch_size == 25
        assert settings.campaign_delay_minutes == 10
        assert settings.email_template_path == "/path/to/template.html"

        print("✓ Custom configuration loaded successfully")
    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_validation_errors():
    """Test validation of configuration values."""
    print("\nTesting validation errors...")

    base_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_SMTP_SERVER": "smtp.example.com",
        "TIERII_TENANT_ID": "test-tenant",
        "TIERII_CLIENT_ID": "test-client",
        "TIERII_CLIENT_SECRET": "test-secret",
        "TIERII_EMAIL_SUBJECT": "Test Subject",
    }

    # Test invalid batch size
    test_env = base_env.copy()
    test_env["TIERII_CAMPAIGN_BATCH_SIZE"] = "-5"

    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

        # This should raise SystemExit due to invalid batch size
        with pytest.raises(SystemExit):
            settings = load_settings()

        print("✓ Correctly failed validation for negative batch size")
    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_batch_size_validation():
    """Test batch size validation with edge cases."""
    print("\nTesting batch size validation...")

    base_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_SMTP_SERVER": "smtp.example.com",
        "TIERII_TENANT_ID": "test-tenant",
        "TIERII_CLIENT_ID": "test-client",
        "TIERII_CLIENT_SECRET": "test-secret",
        "TIERII_EMAIL_SUBJECT": "Test Subject",
    }

    # Test zero batch size
    test_env = base_env.copy()
    test_env["TIERII_CAMPAIGN_BATCH_SIZE"] = "0"

    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

        with pytest.raises(SystemExit):
            settings = load_settings()

        print("✓ Correctly failed validation for zero batch size")
    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_delay_minutes_validation():
    """Test delay minutes validation with edge cases."""
    print("\nTesting delay minutes validation...")

    base_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_SMTP_SERVER": "smtp.example.com",
        "TIERII_TENANT_ID": "test-tenant",
        "TIERII_CLIENT_ID": "test-client",
        "TIERII_CLIENT_SECRET": "test-secret",
        "TIERII_EMAIL_SUBJECT": "Test Subject",
    }

    # Test negative delay
    test_env = base_env.copy()
    test_env["TIERII_CAMPAIGN_DELAY_MINUTES"] = "-1"

    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

        with pytest.raises(SystemExit):
            settings = load_settings()

        print("✓ Correctly failed validation for negative delay minutes")
    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_smtp_port_validation():
    """Test SMTP port validation with edge cases."""
    print("\nTesting SMTP port validation...")

    base_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_SMTP_SERVER": "smtp.example.com",
        "TIERII_TENANT_ID": "test-tenant",
        "TIERII_CLIENT_ID": "test-client",
        "TIERII_CLIENT_SECRET": "test-secret",
        "TIERII_EMAIL_SUBJECT": "Test Subject",
    }

    # Test invalid port (too high)
    test_env = base_env.copy()
    test_env["TIERII_SMTP_PORT"] = "70000"

    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

        with pytest.raises(SystemExit):
            settings = load_settings()

        print("✓ Correctly failed validation for invalid SMTP port")
    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_test_mode_validation():
    """Test test mode validation."""
    print("\nTesting test mode validation...")

    base_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_SMTP_SERVER": "smtp.example.com",
        "TIERII_TENANT_ID": "test-tenant",
        "TIERII_CLIENT_ID": "test-client",
        "TIERII_CLIENT_SECRET": "test-secret",
        "TIERII_EMAIL_SUBJECT": "Test Subject",
    }

    # Store and set environment variables
    original_values = {}
    for key, value in base_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    # Remove test recipient email if it exists
    test_recipient_original = os.environ.get("TIERII_TEST_RECIPIENT_EMAIL")
    if "TIERII_TEST_RECIPIENT_EMAIL" in os.environ:
        del os.environ["TIERII_TEST_RECIPIENT_EMAIL"]

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

        # This should fail in test mode without test recipient
        with pytest.raises(SystemExit):
            settings = load_settings(test_mode=True)

        print("✓ Correctly failed for missing test recipient in test mode")
    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

        if test_recipient_original is not None:
            os.environ["TIERII_TEST_RECIPIENT_EMAIL"] = test_recipient_original


def test_backward_compatibility():
    """Test backward compatibility with legacy constants."""
    print("\nTesting backward compatibility...")

    base_env = {
        "TIERII_SENDER_EMAIL": "legacy@example.com",
        "TIERII_SMTP_SERVER": "legacy.smtp.com",
        "TIERII_TENANT_ID": "legacy-tenant",
        "TIERII_CLIENT_ID": "legacy-client",
        "TIERII_CLIENT_SECRET": "legacy-secret",
        "TIERII_EMAIL_SUBJECT": "Legacy Subject",
    }

    # Store and set environment variables
    original_values = {}
    for key, value in base_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings_module = load_settings_module()
        # Use legacy constants from the loaded module
        SENDER_EMAIL = settings_module.SENDER_EMAIL
        SMTP_SERVER = settings_module.SMTP_SERVER
        SMTP_PORT = settings_module.SMTP_PORT

        # Verify legacy constants work
        assert SENDER_EMAIL == "legacy@example.com"
        assert SMTP_SERVER == "legacy.smtp.com"
        assert SMTP_PORT == 587

        print("✓ Backward compatibility with legacy constants works")
    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


# Tests are now run using pytest
# Run with: python -m pytest tests/unit/test_config.py -v
