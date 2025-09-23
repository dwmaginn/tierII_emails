#!/usr/bin/env python3
"""
Minimal test to debug pydantic-settings environment variable loading
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Set environment variables
os.environ["TEST_EMAIL"] = "test@example.com"
os.environ["TEST_SERVER"] = "smtp.example.com"

print("Environment variables:")
print(f"  TEST_EMAIL = {os.environ.get('TEST_EMAIL')}")
print(f"  TEST_SERVER = {os.environ.get('TEST_SERVER')}")


class SimpleSettings1(BaseSettings):
    model_config = SettingsConfigDict()

    email: str = Field(alias="TEST_EMAIL")
    server: str = Field(alias="TEST_SERVER")


class SimpleSettings2(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    test_email: str
    test_server: str


class SimpleSettings3(BaseSettings):
    TEST_EMAIL: str
    TEST_SERVER: str


print("\nTrying SimpleSettings1 (with alias)...")
try:
    settings = SimpleSettings1()
    print(f"✓ Success: email={settings.email}, server={settings.server}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\nTrying SimpleSettings2 (with env_prefix)...")
try:
    settings = SimpleSettings2()
    print(
        f"✓ Success: test_email={settings.test_email}, test_server={settings.test_server}"
    )
except Exception as e:
    print(f"✗ Failed: {e}")

print("\nTrying SimpleSettings3 (direct field names)...")
try:
    settings = SimpleSettings3()
    print(
        f"✓ Success: TEST_EMAIL={settings.TEST_EMAIL}, TEST_SERVER={settings.TEST_SERVER}"
    )
except Exception as e:
    print(f"✗ Failed: {e}")
