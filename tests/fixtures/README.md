# Configuration Test Fixtures

This directory contains test fixtures for different user configurations in the TierII email system. These fixtures enable comprehensive testing of the email workflow with different authentication providers while ensuring test safety.

## Overview

The fixtures provide complete environment configurations for:
- **David's Setup**: Microsoft 365 OAuth 2.0 authentication
- **Luke's Setup**: Gmail SMTP with App Password authentication

All fixtures are configured to:
- Use `testdata.csv` instead of production data
- Enable dry-run mode to prevent actual email sending
- Provide isolated test environments

## Available Fixtures

### David's Microsoft OAuth Configuration

```python
from tests.fixtures import get_david_config, apply_david_config, clear_david_config

# Get configuration as dictionary
config = get_david_config()

# Apply configuration to environment
apply_david_config()

# Clean up configuration
clear_david_config()
```

**Configuration Details:**
- **Email**: `david@honestpharmco.com`
- **SMTP Server**: `smtp.office365.com`
- **Auth Provider**: `microsoft`
- **Test Data**: Points to `testdata.csv`
- **Dry Run**: Enabled by default

### Luke's Gmail SMTP Configuration

```python
from tests.fixtures import get_luke_config, apply_luke_config, clear_luke_config

# Get configuration as dictionary
config = get_luke_config()

# Apply configuration to environment
apply_luke_config()

# Clean up configuration
clear_luke_config()
```

**Configuration Details:**
- **Email**: `edwards.lukec@gmail.com`
- **SMTP Server**: `smtp.gmail.com`
- **Auth Provider**: `gmail`
- **Test Data**: Points to `testdata.csv`
- **Dry Run**: Enabled by default

## Using Fixtures in Tests

### Method 1: Manual Setup/Teardown

```python
import pytest
from tests.fixtures import apply_david_config, clear_david_config

class TestDavidWorkflow:
    def setup_method(self):
        apply_david_config()
    
    def teardown_method(self):
        clear_david_config()
    
    def test_something(self):
        # Test with David's configuration
        pass
```

### Method 2: Using Pytest Fixtures

```python
import pytest

def test_david_workflow(david_config_fixture):
    # Configuration is automatically applied and cleaned up
    from src.config.settings import load_settings
    settings = load_settings()
    assert settings.auth_provider == "microsoft"

def test_luke_workflow(luke_config_fixture):
    # Configuration is automatically applied and cleaned up
    from src.config.settings import load_settings
    settings = load_settings()
    assert settings.auth_provider == "gmail"
```

### Method 3: Isolated Environment

```python
def test_config_switching(isolated_config):
    # Clean environment guaranteed
    apply_david_config()
    # ... test David's config ...
    
    clear_david_config()
    apply_luke_config()
    # ... test Luke's config ...
    
    # Environment automatically restored after test
```

## Running Configuration Tests

### Run All Configuration Tests

```bash
# Run all integration tests
pytest tests/integration/test_config_workflows.py -v

# Run with coverage
pytest tests/integration/test_config_workflows.py -v --cov=src --cov-report=term-missing
```

### Run Specific Test Categories

```bash
# David's Microsoft OAuth tests
pytest tests/integration/test_config_workflows.py::TestDavidMicrosoftWorkflow -v

# Luke's Gmail SMTP tests
pytest tests/integration/test_config_workflows.py::TestLukeGmailWorkflow -v

# Configuration isolation tests
pytest tests/integration/test_config_workflows.py::TestConfigurationIsolation -v

# Test data safety tests
pytest tests/integration/test_config_workflows.py::TestTestDataSafety -v
```

### Using the Test Runner Script

```bash
# Run all configuration tests with detailed output
python tests/run_config_tests.py
```

## Test Data Safety

### Automatic Test Data Usage

All fixtures automatically configure the system to use `testdata.csv` instead of production data:

```python
# Both configurations include:
"TIERII_CSV_FILE_PATH": "c:/Users/73spi/Work/tierII_emails/data/test/testdata.csv"
```

### Dry Run Mode

All fixtures enable dry run mode by default to prevent actual email sending:

```python
# Both configurations include:
"TIERII_DRY_RUN": "true"
```

### Test Email Addresses

The `testdata.csv` file contains safe test email addresses:
- `edwards.lukec@gmail.com`
- `73spider73@gmail.com`
- `lce1868@rit.edu`

## Configuration Validation

The fixtures include validation to ensure:

1. **Correct Authentication Provider**: Microsoft vs Gmail
2. **Proper SMTP Settings**: Server, port, credentials
3. **Test Data Path**: Points to `testdata.csv`
4. **Safety Settings**: Dry run enabled, test recipient configured
5. **Environment Isolation**: Clean setup and teardown

## Best Practices

### 1. Always Use Fixtures for Integration Tests

```python
# Good: Uses fixture for automatic cleanup
def test_workflow(david_config_fixture):
    # Test code here
    pass

# Avoid: Manual setup without guaranteed cleanup
def test_workflow():
    apply_david_config()  # What if test fails?
    # Test code here
    clear_david_config()  # Might not execute
```

### 2. Test Configuration Isolation

```python
def test_config_switching():
    # Test that switching between configs works properly
    apply_david_config()
    settings1 = load_settings()
    
    clear_david_config()
    apply_luke_config()
    settings2 = load_settings()
    
    assert settings1.auth_provider != settings2.auth_provider
```

### 3. Verify Test Data Usage

```python
def test_uses_test_data(david_config_fixture):
    from src.utils.csv_reader import load_contacts
    contacts = load_contacts()
    
    # Verify we're using test data
    assert len(contacts) == 3  # testdata.csv has 3 records
    test_emails = [c['Email'] for c in contacts]
    assert "edwards.lukec@gmail.com" in test_emails
```

## Troubleshooting

### Configuration Not Loading

1. Check that fixtures are properly imported
2. Verify `setup_method`/`teardown_method` are called
3. Ensure environment variables are set correctly

### Tests Interfering with Each Other

1. Use `isolated_config` fixture for complete isolation
2. Always call `clear_*_config()` in teardown
3. Check for leftover environment variables

### Import Errors

1. Ensure `tests/fixtures/__init__.py` exists
2. Check Python path includes project root
3. Verify all dependencies are installed

## File Structure

```
tests/fixtures/
├── __init__.py              # Package initialization and exports
├── david_config.py          # David's Microsoft OAuth configuration
├── luke_config.py           # Luke's Gmail SMTP configuration
└── README.md               # This documentation
```

## Related Files

- `tests/integration/test_config_workflows.py` - Integration tests using these fixtures
- `tests/conftest.py` - Pytest fixtures for easy usage
- `tests/run_config_tests.py` - Test runner script
- `data/test/testdata.csv` - Test data file used by all fixtures