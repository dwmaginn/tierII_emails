# Development Guide

Comprehensive guide for developers contributing to the TierII Email Campaign system, covering setup, workflows, testing, and best practices.

## 📋 Overview

This guide is designed for developers who want to contribute to the TierII Email Campaign system. It covers everything from initial development environment setup to advanced contribution workflows, following Test-Driven Development (TDD) principles.

## 🚀 Development Environment Setup

### Prerequisites

#### Required Software
```bash
# Python 3.8 or higher
python --version  # Should be 3.8+

# Git for version control
git --version

# Optional but recommended
pip install pipenv  # For virtual environment management
```

#### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 1GB free space for development environment
- **Network**: Internet connection for API testing and dependencies

### Initial Setup

#### 1. Clone and Setup Repository
```bash
# Clone the repository
git clone https://github.com/your-org/tierII_emails.git
cd tierII_emails

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 2. Development Dependencies
```bash
# Core development tools
pip install pytest pytest-cov black flake8 mypy pre-commit

# Additional testing tools
pip install pytest-mock pytest-asyncio factory-boy

# Documentation tools
pip install mkdocs mkdocs-material

# Optional: Install in development mode
pip install -e .
```

#### 3. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env.dev

# Edit .env.dev with development settings
# Use test API tokens and development email addresses
```

#### 4. Pre-commit Hooks Setup
```bash
# Install pre-commit hooks
pre-commit install

# Test pre-commit hooks
pre-commit run --all-files
```

### Development Tools Configuration

#### VS Code Configuration
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm Configuration
```python
# Configure PyCharm for the project
# 1. Set Python interpreter to venv/bin/python
# 2. Enable pytest as test runner
# 3. Configure Black as code formatter
# 4. Enable flake8 and mypy inspections
```

## 🔄 Test-Driven Development (TDD) Workflow

### TDD Cycle: Red-Green-Refactor

#### 1. RED: Write Failing Tests First
```python
# tests/test_email_campaign.py
import pytest
from tierII_email_campaign.email_campaign import EmailCampaign
from tierII_email_campaign.exceptions import ValidationError

class TestEmailCampaign:
    """Test cases for EmailCampaign class."""
    
    def test_campaign_initialization_with_valid_config(self):
        """Test that campaign initializes correctly with valid configuration."""
        # This test should fail initially (RED)
        config = {
            'sender_email': 'test@example.com',
            'api_token': 'test-token',
            'batch_size': 50
        }
        
        campaign = EmailCampaign(config)
        
        assert campaign.sender_email == 'test@example.com'
        assert campaign.batch_size == 50
        assert campaign.is_configured is True
    
    def test_campaign_raises_error_with_invalid_email(self):
        """Test that campaign raises ValidationError with invalid sender email."""
        # This test should fail initially (RED)
        config = {
            'sender_email': 'invalid-email',
            'api_token': 'test-token'
        }
        
        with pytest.raises(ValidationError, match="Invalid sender email format"):
            EmailCampaign(config)
```

#### 2. GREEN: Write Minimal Code to Pass Tests
```python
# tierII_email_campaign/email_campaign.py
import re
from typing import Dict, Any
from .exceptions import ValidationError

class EmailCampaign:
    """Email campaign management class."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize email campaign with configuration."""
        self.sender_email = config.get('sender_email')
        self.api_token = config.get('api_token')
        self.batch_size = config.get('batch_size', 50)
        
        # Validate configuration
        self._validate_config()
        
        self.is_configured = True
    
    def _validate_config(self):
        """Validate campaign configuration."""
        if not self._is_valid_email(self.sender_email):
            raise ValidationError("Invalid sender email format")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
```

#### 3. REFACTOR: Improve Code While Keeping Tests Green
```python
# Refactored version with better structure
from dataclasses import dataclass
from typing import Optional
import re
from src.config.settings import TierIISettings

class EmailCampaign:
    """Email campaign management class."""
    
    def __init__(self, csv_file: str, auth_manager=None, batch_size: int = 50, delay_minutes: int = 30):
        """Initialize email campaign with CSV file and configuration."""
        self.csv_file = csv_file
        self.auth_manager = auth_manager
        self.batch_size = batch_size
        self.delay_minutes = delay_minutes
        self.is_configured = True
    
    @property
    def sender_email(self) -> str:
        """Get sender email from configuration."""
        settings = TierIISettings()
        return settings.sender_email
    
    def load_contacts(self):
        """Load contacts from CSV file."""
        from src.utils.csv_reader import load_contacts
        return load_contacts(self.csv_file)
    
    def send_campaign(self, template_path: str):
        """Send email campaign using template."""
        # Implementation would use the authentication manager
        # and send emails in batches with delays
        pass
```

### Testing Strategy

#### Test Categories and Coverage Requirements

1. **Unit Tests** (Target: 90%+ coverage)
   - Test individual functions and methods
   - Mock external dependencies
   - Fast execution (< 1 second per test)

2. **Integration Tests** (Target: 80%+ coverage)
   - Test component interactions
   - Use test containers for external services
   - Medium execution time (< 10 seconds per test)

3. **End-to-End Tests** (Target: 70%+ coverage)
   - Test complete workflows
   - Use staging environment
   - Slower execution (< 60 seconds per test)

#### Test Structure and Organization
```
tests/
├── unit/
│   ├── test_authentication.py
│   ├── test_email_campaign.py
│   ├── test_csv_reader.py
│   └── test_settings.py
├── integration/
│   ├── test_mailersend_integration.py
│   ├── test_campaign_workflow.py
│   └── test_template_rendering.py
├── e2e/
│   ├── test_full_campaign.py
│   └── test_error_recovery.py
├── fixtures/
│   ├── sample_contacts.csv
│   ├── test_templates/
│   └── mock_responses.json
└── conftest.py
```

#### Test Fixtures and Factories
```python
# tests/conftest.py
import pytest
from unittest.mock import Mock
from tierII_email_campaign.settings import Settings
from tierII_email_campaign.email_campaign import EmailCampaign

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.sender_email = "test@example.com"
    settings.mailersend_api_token = "test-token"
    settings.batch_size = 10
    settings.delay_minutes = 1
    return settings

@pytest.fixture
def sample_email_campaign():
    """Sample email campaign for testing."""
    return EmailCampaign(
        csv_file="test_contacts.csv",
        batch_size=10,
        delay_minutes=1
    )

@pytest.fixture
def sample_contacts():
    """Sample contact data for testing."""
    return [
        {
            'email': 'john.doe@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'company': 'Acme Corp'
        },
        {
            'email': 'jane.smith@example.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'company': 'Beta LLC'
        }
    ]

@pytest.fixture
def mock_mailersend_client():
    """Mock MailerSend client for testing."""
    client = Mock()
    client.send_email.return_value = {'success': True, 'message_id': 'test-123'}
    return client
```

#### Factory Pattern for Test Data
```python
# tests/factories.py
import factory
from faker import Faker

fake = Faker()

def create_test_contact_dict():
    """Factory for creating test contact dictionaries."""
    return {
        'email': fake.email(),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'company': fake.company(),
        'position': fake.job()
    }

def create_test_campaign_result():
    """Factory for creating test campaign result dictionaries."""
    return {
        'campaign_id': fake.uuid4(),
        'total_contacts': 100,
        'successful_sends': 95,
        'failed_sends': 5,
        'start_time': fake.date_time(),
        'end_time': fake.date_time()
    }

# Usage in tests
def test_contact_validation():
    """Test contact validation with factory-generated data."""
    contact = create_test_contact_dict()
    assert '@' in contact['email']
    assert '.' in contact['email']
    
def test_campaign_with_multiple_contacts():
    """Test campaign with multiple factory-generated contacts."""
    contacts = [create_test_contact_dict() for _ in range(50)]
    # Test campaign logic with contacts
```

### Code Quality Standards

#### Code Formatting with Black
```python
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

#### Linting with Flake8
```ini
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    .venv,
    build,
    dist,
    *.egg-info
per-file-ignores =
    __init__.py:F401
    tests/*:S101
```

#### Type Checking with MyPy
```ini
# mypy.ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-tests.*]
disallow_untyped_defs = False
```

#### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
```

## 🔧 Development Workflow

### Feature Branch Workflow

#### 1. Create Feature Branch
```bash
# Create and switch to feature branch
git checkout -b feature/sprint-1/email-template-engine

# Verify branch
git branch
```

#### 2. TDD Development Cycle
```bash
# 1. Write failing tests
# Edit tests/test_template_engine.py

# 2. Run tests (should fail - RED)
pytest tests/test_template_engine.py -v

# 3. Write minimal implementation
# Edit tierII_email_campaign/template_engine.py

# 4. Run tests (should pass - GREEN)
pytest tests/test_template_engine.py -v

# 5. Refactor code
# Improve implementation while keeping tests green

# 6. Run full test suite
pytest --cov=tierII_email_campaign --cov-report=html
```

#### 3. Code Quality Checks
```bash
# Format code
black .

# Check linting
flake8

# Type checking
mypy tierII_email_campaign/

# Run all pre-commit hooks
pre-commit run --all-files
```

#### 4. Commit Changes
```bash
# Stage changes
git add .

# Commit with conventional format
git commit -m "feat(template): add Jinja2 template engine support

- Implement TemplateEngine class with Jinja2 backend
- Add template validation and error handling
- Support for custom template functions
- Add comprehensive test coverage (95%)

Closes #123"
```

### Testing Workflow

#### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_email_campaign.py

# Run tests with coverage
pytest --cov=tierII_email_campaign --cov-report=html

# Run tests in parallel
pytest -n auto

# Run only failed tests
pytest --lf

# Run tests with verbose output
pytest -v

# Run specific test method
pytest tests/test_email_campaign.py::TestEmailCampaign::test_send_campaign
```

#### Test Coverage Requirements
```bash
# Check coverage and enforce minimum threshold
pytest --cov=tierII_email_campaign --cov-fail-under=80

# Generate HTML coverage report
pytest --cov=tierII_email_campaign --cov-report=html
open htmlcov/index.html  # View coverage report
```

#### Integration Testing with Test Containers
```python
# tests/integration/test_mailersend_integration.py
import pytest
from testcontainers.compose import DockerCompose
from tierII_email_campaign.providers.mailersend import MailerSendProvider

@pytest.fixture(scope="module")
def mailersend_mock_server():
    """Start mock MailerSend server for integration testing."""
    with DockerCompose("tests/docker", compose_file_name="docker-compose.test.yml") as compose:
        # Wait for services to be ready
        compose.wait_for("http://localhost:8080/health")
        yield compose

def test_mailersend_integration(mailersend_mock_server):
    """Test MailerSend integration with mock server."""
    provider = MailerSendProvider(
        api_token="test-token",
        base_url="http://localhost:8080"
    )
    
    result = provider.send_email(
        to_email="test@example.com",
        subject="Test Email",
        content="Test content"
    )
    
    assert result.success is True
    assert result.message_id is not None
```

### Debugging and Development Tools

#### Logging Configuration for Development
```python
# development_logging.py
import logging
import sys
from pathlib import Path

def setup_development_logging():
    """Configure logging for development environment."""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "development.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configure specific loggers
    logging.getLogger('tierII_email_campaign').setLevel(logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

# Use in development
if __name__ == "__main__":
    setup_development_logging()
```

#### Development CLI Tools
```python
# dev_tools.py
import click
from tierII_email_campaign.settings import Settings
from tierII_email_campaign.providers.mailersend import MailerSendProvider

@click.group()
def cli():
    """Development tools for TierII Email Campaign."""
    pass

@cli.command()
def test_connection():
    """Test MailerSend API connection."""
    settings = Settings()
    provider = MailerSendProvider(settings.mailersend_api_token)
    
    try:
        result = provider.test_connection()
        if result.success:
            click.echo("✅ Connection successful")
        else:
            click.echo(f"❌ Connection failed: {result.error}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.argument('template_path')
def validate_template(template_path):
    """Validate email template."""
    from tierII_email_campaign.template_engine import validate_template
    
    try:
        validate_template(template_path)
        click.echo("✅ Template is valid")
    except Exception as e:
        click.echo(f"❌ Template error: {e}")

@cli.command()
@click.argument('csv_path')
def validate_contacts(csv_path):
    """Validate contact CSV file."""
    from tierII_email_campaign.csv_reader import validate_contact_data
    
    try:
        contacts = validate_contact_data(csv_path)
        click.echo(f"✅ Loaded {len(contacts)} valid contacts")
    except Exception as e:
        click.echo(f"❌ CSV error: {e}")

if __name__ == "__main__":
    cli()
```

### Performance Profiling

#### Memory Profiling
```python
# profile_memory.py
from memory_profiler import profile
from tierII_email_campaign.email_campaign import EmailCampaign

@profile
def profile_campaign_execution():
    """Profile memory usage during campaign execution."""
    
    # Load large contact list
    contacts = load_large_contact_list("tests/fixtures/large_contacts.csv")
    
    # Initialize campaign
    campaign = EmailCampaign(config)
    
    # Process contacts
    results = campaign.send_campaign(contacts)
    
    return results

if __name__ == "__main__":
    profile_campaign_execution()
```

#### Performance Benchmarking
```python
# benchmark.py
import time
import statistics
from typing import List, Callable

def benchmark_function(func: Callable, iterations: int = 10) -> dict:
    """Benchmark function execution time."""
    
    times = []
    for _ in range(iterations):
        start_time = time.perf_counter()
        func()
        end_time = time.perf_counter()
        times.append(end_time - start_time)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times)
    }

# Usage
def test_contact_loading():
    """Benchmark contact loading performance."""
    from src.utils.csv_reader import load_contacts
    load_contacts("data/tier_i_tier_ii_emails_verified.csv")

results = benchmark_function(test_contact_loading, iterations=20)
print(f"Contact loading benchmark: {results}")
```

## 📚 Documentation Development

### Documentation Standards

#### Docstring Format (Google Style)
```python
def send_email_campaign(
    contacts: List[Dict[str, Any]],
    template_path: str,
    batch_size: int = 50,
    delay_minutes: int = 30
) -> Dict[str, Any]:
    """Send email campaign to list of contacts.
    
    This function orchestrates the entire email campaign process, including
    template rendering, batch processing, and error handling.
    
    Args:
        contacts: List of validated contact dictionaries to send emails to.
        template_path: Path to the email template file (HTML format).
        batch_size: Number of emails to send per batch.
        delay_minutes: Delay between batches in minutes.
    
    Returns:
        Dictionary containing send statistics and any errors with keys:
        - total_contacts: Total number of contacts processed
        - successful_sends: Number of successful email sends
        - failed_sends: Number of failed email sends
        - start_time: Campaign start timestamp
        - end_time: Campaign end timestamp
        - errors: List of error messages if any
    
    Raises:
        ValidationError: If contacts or template validation fails.
        AuthenticationError: If email provider authentication fails.
        TemplateError: If template rendering fails.
    
    Example:
        >>> contacts = load_contacts("contacts.csv")
        >>> result = send_email_campaign(contacts, "template.html", batch_size=50, delay_minutes=30)
        >>> print(f"Sent {result['successful_sends']} emails")
    """
    # Implementation here
```

#### API Documentation Generation
```bash
# Generate API documentation with Sphinx
pip install sphinx sphinx-autodoc-typehints

# Initialize Sphinx documentation
sphinx-quickstart docs/api

# Generate API docs
sphinx-apidoc -o docs/api/source tierII_email_campaign/

# Build documentation
cd docs/api
make html
```

### Contributing Guidelines

#### Pull Request Process

1. **Branch Naming Convention**
   ```bash
   feature/sprint-X/feature-name
   bugfix/issue-number/bug-description
   hotfix/critical-issue-description
   docs/documentation-update
   ```

2. **Commit Message Format**
   ```
   type(scope): description
   
   [optional body]
   
   [optional footer]
   ```
   
   Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

3. **Pull Request Template**
   ```markdown
   ## Description
   Brief description of changes and motivation.
   
   ## Type of Change
   - [ ] Bug fix (non-breaking change which fixes an issue)
   - [ ] New feature (non-breaking change which adds functionality)
   - [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
   - [ ] Documentation update
   
   ## Testing
   - [ ] Tests pass locally with my changes
   - [ ] I have added tests that prove my fix is effective or that my feature works
   - [ ] New and existing unit tests pass locally with my changes
   - [ ] Coverage remains above 80%
   
   ## Checklist
   - [ ] My code follows the style guidelines of this project
   - [ ] I have performed a self-review of my own code
   - [ ] I have commented my code, particularly in hard-to-understand areas
   - [ ] I have made corresponding changes to the documentation
   - [ ] My changes generate no new warnings
   ```

#### Code Review Guidelines

**For Authors:**
- Ensure all tests pass and coverage is maintained
- Write clear commit messages and PR descriptions
- Respond to feedback promptly and professionally
- Update documentation as needed

**For Reviewers:**
- Focus on code quality, security, and maintainability
- Provide constructive feedback with suggestions
- Test the changes locally when possible
- Approve only when confident in the changes

## 🔒 Security Considerations

### Secure Development Practices

#### 1. Secrets Management
```python
# Never commit secrets to version control
# Use environment variables or secure vaults

# Good: Load from environment
api_token = os.getenv('TIERII_MAILERSEND_API_TOKEN')

# Bad: Hardcoded secrets
api_token = "mlsn.1234567890abcdef"  # Never do this!
```

#### 2. Input Validation
```python
def validate_email_input(email: str) -> str:
    """Validate and sanitize email input."""
    
    # Remove whitespace
    email = email.strip()
    
    # Validate format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValidationError("Invalid email format")
    
    # Check for suspicious patterns
    if any(pattern in email.lower() for pattern in ['script', 'javascript', '<', '>']):
        raise SecurityError("Potentially malicious email address")
    
    return email.lower()
```

#### 3. Dependency Security
```bash
# Regularly check for security vulnerabilities
pip install safety
safety check

# Update dependencies regularly
pip-review --local --interactive
```

## 📚 Related Documentation

- **[Quick Start Guide](../quick-start.md)** - Get started quickly
- **[Testing Guide](testing.md)** - Comprehensive testing documentation
- **[Architecture Overview](../architecture/overview.md)** - System architecture
- **[Contributing Guidelines](contributing.md)** - How to contribute
- **[API Reference](../api/)** - Complete API documentation

---

**Development Guide Version**: 0.1.0  
**TDD Methodology**: Red-Green-Refactor cycle  
**Coverage Target**: 80% minimum, 90% recommended  
**Code Quality**: Black + Flake8 + MyPy + Pre-commit hooks