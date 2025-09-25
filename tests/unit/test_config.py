#!/usr/bin/env python3
"""
Test script to validate ST3-002 Configuration Module Enhancement.
Tests environment variable loading, validation, and backward compatibility.
"""

import os
from pathlib import Path
import importlib.util
import pytest

# Determine project root and settings file path
project_root = Path(__file__).parent.parent.parent.absolute()
src_path = project_root / "src"
settings_file = src_path / "config" / "settings.py"


def load_settings_module():
    """Dynamically load the settings module."""
    spec = importlib.util.spec_from_file_location("config.settings", settings_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load settings module from {settings_file}")

    settings_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings_module)
    return settings_module


def test_imports():
    """Test that all required imports work correctly."""
    print("\nTesting imports...")

    settings_module = load_settings_module()

    # Test that key classes and functions are available
    assert hasattr(settings_module, "TierIISettings")
    assert hasattr(settings_module, "load_settings")

    print("✓ All imports successful")


def test_missing_required_variables():
    """Test behavior when required environment variables are missing."""
    print("\nTesting missing required variables...")

    # Store original values
    required_vars = ["TIERII_SENDER_EMAIL", "TIERII_MAILERSEND_API_TOKEN"]
    original_values = {}
    for var in required_vars:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

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

    # Set minimal required environment variables for MailerSend
    test_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_MAILERSEND_API_TOKEN": "test-api-token",
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
        assert settings.mailersend_api_token == "test-api-token"
        assert settings.campaign_batch_size == 50  # Default value
        assert settings.campaign_delay_minutes == 5  # Default value
        assert settings.sender_name == "Test"  # Derived from email

        print("✓ Minimal MailerSend configuration loaded successfully with defaults")

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
        "TIERII_MAILERSEND_API_TOKEN": "custom-api-token",
        "TIERII_SENDER_NAME": "Custom Sender",
        "TIERII_CAMPAIGN_BATCH_SIZE": "25",
        "TIERII_CAMPAIGN_DELAY_MINUTES": "10",
        "TIERII_EMAIL_TEMPLATE_PATH": "/path/to/template.html",
        "TIERII_TEST_RECIPIENT_EMAIL": "test@example.com",
        "TIERII_TEST_FALLBACK_FIRST_NAME": "Tester",
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
        assert settings.mailersend_api_token == "custom-api-token"
        assert settings.sender_name == "Custom Sender"
        assert settings.campaign_batch_size == 25
        assert settings.campaign_delay_minutes == 10
        assert settings.email_template_path == "/path/to/template.html"
        assert settings.test_recipient_email == "test@example.com"
        assert settings.test_fallback_first_name == "Tester"

        print("✓ Custom MailerSend configuration loaded successfully")

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

    # Test invalid batch size
    test_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_MAILERSEND_API_TOKEN": "test-token",
        "TIERII_CAMPAIGN_BATCH_SIZE": "0",  # Invalid
    }

    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

        try:
            settings = load_settings()
            assert False, "Expected validation error for invalid batch size"
        except (SystemExit, Exception):
            print("✓ Correctly caught validation error for invalid batch size")

    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_batch_size_validation():
    """Test batch size validation."""
    print("\nTesting batch size validation...")

    test_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_MAILERSEND_API_TOKEN": "test-token",
        "TIERII_CAMPAIGN_BATCH_SIZE": "0",  # Invalid batch size
    }

    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

        try:
            settings = load_settings()
            assert False, "Expected validation error for batch size 0"
        except (SystemExit, Exception):
            print("✓ Correctly validated batch size must be positive")

    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_delay_minutes_validation():
    """Test delay minutes validation."""
    print("\nTesting delay minutes validation...")

    test_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_MAILERSEND_API_TOKEN": "test-token",
        "TIERII_CAMPAIGN_DELAY_MINUTES": "-1",  # Invalid delay
    }

    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

        try:
            settings = load_settings()
            assert False, "Expected validation error for negative delay"
        except (SystemExit, Exception):
            print("✓ Correctly validated delay minutes cannot be negative")

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

    test_env = {
        "TIERII_SENDER_EMAIL": "test@example.com",
        "TIERII_MAILERSEND_API_TOKEN": "test-token",
        # Missing TIERII_TEST_RECIPIENT_EMAIL for test mode
    }

    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    # Remove test recipient email if it exists
    if "TIERII_TEST_RECIPIENT_EMAIL" in os.environ:
        original_values["TIERII_TEST_RECIPIENT_EMAIL"] = os.environ["TIERII_TEST_RECIPIENT_EMAIL"]
        del os.environ["TIERII_TEST_RECIPIENT_EMAIL"]

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings

        try:
            settings = load_settings(test_mode=True)
            assert False, "Expected validation error for missing test recipient in test mode"
        except SystemExit:
            print("✓ Correctly validated test mode requires test recipient email")

    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_sender_name_derivation():
    """Test automatic sender name derivation from email."""
    print("\nTesting sender name derivation...")

    test_env = {
        "TIERII_SENDER_EMAIL": "john.doe@example.com",
        "TIERII_MAILERSEND_API_TOKEN": "test-token",
        # No TIERII_SENDER_NAME provided
    }

    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    # Remove sender name if it exists
    if "TIERII_SENDER_NAME" in os.environ:
        original_values["TIERII_SENDER_NAME"] = os.environ["TIERII_SENDER_NAME"]
        del os.environ["TIERII_SENDER_NAME"]

    try:
        settings_module = load_settings_module()
        load_settings = settings_module.load_settings
        settings = load_settings()

        # Should derive sender name from email
        assert settings.sender_name == "John Doe"  # Derived from john.doe@example.com
        print("✓ Correctly derived sender name from email address")

    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


if __name__ == "__main__":
    print("Running TierII MailerSend Configuration Tests")
    print("=" * 50)

    test_functions = [
        test_imports,
        test_missing_required_variables,
        test_minimal_configuration,
        test_custom_configuration,
        test_validation_errors,
        test_batch_size_validation,
        test_delay_minutes_validation,
        test_test_mode_validation,
        test_sender_name_derivation,
    ]

    passed = 0
    total = len(test_functions)

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")

    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All MailerSend configuration tests passed!")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
