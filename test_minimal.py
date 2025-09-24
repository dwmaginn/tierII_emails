#!/usr/bin/env python3
"""Minimal test to debug import issue."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports (exactly like the test)
src_path = os.path.join(os.path.dirname(__file__), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print(f"Added src_path: {src_path}")
print(f"sys.path first 3 entries: {sys.path[:3]}")

try:
    from auth.base_authentication_manager import (
        AuthenticationProvider,
        AuthenticationError,
        TokenExpiredError,
        InvalidCredentialsError,
        NetworkError
    )
    print("✓ Successfully imported from auth.base_authentication_manager")
except Exception as e:
    print(f"✗ Failed to import from auth.base_authentication_manager: {e}")

try:
    from email_campaign import main
    print("✓ Successfully imported email_campaign.main")
except Exception as e:
    print(f"✗ Failed to import email_campaign.main: {e}")
    import traceback
    traceback.print_exc()

print("\nTest completed successfully!")