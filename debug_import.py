#!/usr/bin/env python3
"""Debug script to test imports."""

import sys
import os

# Add src to path like the test does
src_path = os.path.join(os.path.dirname(__file__), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print(f"Python path: {sys.path[:3]}...")
print(f"Current working directory: {os.getcwd()}")
print(f"Src path: {src_path}")
print(f"Src path exists: {os.path.exists(src_path)}")

try:
    print("\nTrying to import config.settings...")
    from config.settings import load_settings
    print("✓ config.settings imported successfully")
except Exception as e:
    print(f"✗ Failed to import config.settings: {e}")
    print(f"Error type: {type(e)}")

try:
    print("\nTrying to import email_campaign...")
    from email_campaign import main
    print("✓ email_campaign imported successfully")
except Exception as e:
    print(f"✗ Failed to import email_campaign: {e}")
    print(f"Error type: {type(e)}")

print("\nChecking config directory:")
config_path = os.path.join(src_path, "config")
print(f"Config path: {config_path}")
print(f"Config path exists: {os.path.exists(config_path)}")
if os.path.exists(config_path):
    print(f"Config contents: {os.listdir(config_path)}")

print("\nChecking __init__.py files:")
for root, dirs, files in os.walk(src_path):
    if "__init__.py" in files:
        init_path = os.path.join(root, "__init__.py")
        rel_path = os.path.relpath(init_path, src_path)
        print(f"Found __init__.py: {rel_path}")