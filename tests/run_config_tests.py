#!/usr/bin/env python3
"""Test runner for configuration-specific integration tests.

This script demonstrates how to run the configuration workflow tests
for both David's Microsoft OAuth and Luke's Gmail SMTP setups.

Usage:
    python tests/run_config_tests.py
    
Or run specific test categories:
    pytest tests/integration/test_config_workflows.py::TestDavidMicrosoftWorkflow -v
    pytest tests/integration/test_config_workflows.py::TestLukeGmailWorkflow -v
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    """Run configuration workflow tests."""
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    print(f"Project root: {project_root.absolute()}")
    
    # Test commands to run
    test_commands = [
        {
            "cmd": [
                sys.executable, "-m", "pytest", 
                "tests/integration/test_config_workflows.py::TestDavidMicrosoftWorkflow",
                "-v", "--tb=short", "-m", "integration"
            ],
            "description": "David's Microsoft OAuth Configuration Tests"
        },
        {
            "cmd": [
                sys.executable, "-m", "pytest", 
                "tests/integration/test_config_workflows.py::TestLukeGmailWorkflow",
                "-v", "--tb=short", "-m", "integration"
            ],
            "description": "Luke's Gmail SMTP Configuration Tests"
        },
        {
            "cmd": [
                sys.executable, "-m", "pytest", 
                "tests/integration/test_config_workflows.py::TestConfigurationIsolation",
                "-v", "--tb=short", "-m", "integration"
            ],
            "description": "Configuration Isolation Tests"
        },
        {
            "cmd": [
                sys.executable, "-m", "pytest", 
                "tests/integration/test_config_workflows.py::TestTestDataSafety",
                "-v", "--tb=short", "-m", "integration"
            ],
            "description": "Test Data Safety Tests"
        },
        {
            "cmd": [
                sys.executable, "-m", "pytest", 
                "tests/integration/test_config_workflows.py",
                "-v", "--tb=short", "-m", "integration", "--cov=src", "--cov-report=term-missing"
            ],
            "description": "All Configuration Tests with Coverage"
        }
    ]
    
    # Run tests
    success_count = 0
    total_count = len(test_commands)
    
    for test_config in test_commands:
        success = run_command(test_config["cmd"], test_config["description"])
        if success:
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Successful: {success_count}/{total_count}")
    print(f"Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n✅ All configuration tests passed!")
        print("\nBoth David's Microsoft OAuth and Luke's Gmail SMTP configurations")
        print("are working correctly with testdata.csv to prevent unintended emails.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())