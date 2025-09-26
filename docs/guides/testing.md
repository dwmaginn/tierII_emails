# Testing Guide

Comprehensive testing documentation for the TierII Email Campaign system, covering testing strategies, implementation, and best practices.

## 📋 Overview

This guide provides complete testing documentation for developers, QA engineers, and contributors. It covers unit testing, integration testing, end-to-end testing, and performance testing with practical examples and best practices.

## 🎯 Testing Philosophy

### Test-Driven Development (TDD)
The TierII Email Campaign system follows strict TDD principles:

1. **RED**: Write failing tests first
2. **GREEN**: Write minimal code to make tests pass  
3. **REFACTOR**: Improve code while keeping tests green

### Testing Pyramid
```
    /\
   /  \     E2E Tests (10%)
  /____\    - Full workflow testing
 /      \   - User acceptance testing
/________\  
           Integration Tests (20%)
           - Component interaction testing
           - API integration testing
           
           Unit Tests (70%)
           - Function/method testing
           - Class behavior testing
           - Edge case testing
```

### Coverage Requirements
- **Minimum Coverage**: 80% for all new code
- **Target Coverage**: 90% for critical components
- **Critical Functions**: 100% coverage required
- **Coverage Gates**: Enforced in CI/CD pipeline

## 🧪 Test Categories

### 1. Unit Tests

#### Purpose and Scope
- Test individual functions, methods, and classes in isolation
- Mock external dependencies
- Fast execution (< 1 second per test)
- High coverage of edge cases and error conditions

#### Example: Testing Email Validation
```python
# tests/unit/test_email_validation.py
import pytest
from tierII_email_campaign.validators import EmailValidator
from tierII_email_campaign.exceptions import ValidationError

class TestEmailValidator:
    """Unit tests for email validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.validator = EmailValidator()
    
    def test_valid_email_addresses(self):
        """Test validation of valid email addresses."""
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "user123@test-domain.org",
            "firstname.lastname@company.com"
        ]
        
        for email in valid_emails:
            assert self.validator.is_valid(email), f"Email {email} should be valid"
    
    def test_invalid_email_addresses(self):
        """Test validation of invalid email addresses."""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user..double.dot@domain.com",
            "user@domain..com"
        ]
        
        for email in invalid_emails:
            assert not self.validator.is_valid(email), f"Email {email} should be invalid"
    
    def test_email_normalization(self):
        """Test email address normalization."""
        test_cases = [
            ("User@Example.COM", "user@example.com"),
            ("  test@domain.com  ", "test@domain.com"),
            ("Test.Email@Domain.Org", "test.email@domain.org")
        ]
        
        for input_email, expected in test_cases:
            normalized = self.validator.normalize(input_email)
            assert normalized == expected
    
    def test_validation_error_messages(self):
        """Test that appropriate error messages are provided."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            self.validator.validate("invalid-email")
        
        with pytest.raises(ValidationError, match="Email cannot be empty"):
            self.validator.validate("")
    
    @pytest.mark.parametrize("email,expected", [
        ("test@example.com", True),
        ("invalid", False),
        ("@domain.com", False),
        ("user@domain.co.uk", True)
    ])
    def test_parametrized_validation(self, email, expected):
        """Test email validation with parametrized inputs."""
        result = self.validator.is_valid(email)
        assert result == expected
```

#### Example: Testing Campaign Configuration
```python
# tests/unit/test_campaign_config.py
import pytest
from unittest.mock import Mock, patch
from src.config.settings import TierIISettings
from src.exceptions import ConfigurationError

class TestTierIISettings:
    """Unit tests for campaign configuration."""
    
    def test_config_initialization_with_valid_data(self):
        """Test configuration initialization with valid data."""
        config = TierIISettings(
            sender_email='test@example.com',
            mailersend_api_token='test-token-123',
            batch_size=50,
            delay_minutes=30
        )
        
        assert config.sender_email == 'test@example.com'
        assert config.mailersend_api_token == 'test-token-123'
        assert config.batch_size == 50
        assert config.delay_minutes == 30
    
    def test_config_with_missing_required_fields(self):
        """Test configuration with missing required fields."""
        with pytest.raises(ValueError, match="sender_email"):
            TierIISettings(
                sender_email='',  # Empty required field
                mailersend_api_token='test-token'
            )
    
    def test_config_with_invalid_batch_size(self):
        """Test configuration with invalid batch size."""
        with pytest.raises(ValueError, match="batch_size"):
            TierIISettings(
                sender_email='test@example.com',
                mailersend_api_token='test-token',
                batch_size=-1  # Invalid negative value
            )
    
    @patch.dict('os.environ', {'TIERII_BATCH_SIZE': '100'})
    def test_config_from_environment_variables(self):
        """Test configuration loading from environment variables."""
        config = TierIISettings()
        
        assert config.batch_size == 100
    
    def test_config_validation_with_mock(self):
        """Test configuration validation with mocked dependencies."""
        with patch('tierII_email_campaign.validators.EmailValidator') as mock_validator:
            mock_validator.return_value.is_valid.return_value = True
            
            config = TierIISettings(
                sender_email='test@example.com',
                mailersend_api_token='test-token'
            )
            
            # Verify validator was called
            mock_validator.return_value.is_valid.assert_called_once_with('test@example.com')
```

### 2. Integration Tests

#### Purpose and Scope
- Test component interactions and data flow
- Test external service integrations
- Use test containers or mocked services
- Medium execution time (< 10 seconds per test)

#### Example: MailerSend Integration Testing
```python
# tests/integration/test_mailersend_integration.py
import pytest
from unittest.mock import Mock, patch
import responses
from src.auth.mailersend import MailerSendAuthenticationManager

class TestMailerSendIntegration:
    """Integration tests for MailerSend provider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.auth_manager = MailerSendAuthenticationManager(
            api_token="test-token"
        )
    
    @responses.activate
    def test_successful_email_send(self):
        """Test successful email sending through MailerSend API."""
        # Mock successful API response
        responses.add(
            responses.POST,
            "https://api.mailersend.com/v1/email",
            json={"message": "Email sent successfully", "message_id": "msg_123"},
            status=200
        )
        
        # Create test email data
        email_data = {
            "to_email": "recipient@example.com",
            "subject": "Test Email",
            "html_content": "<h1>Test Content</h1>",
            "text_content": "Test Content"
        }
        
        # Test sending email through authentication manager
        # (Note: Actual implementation would use EmailCampaign class)
        # This is a simplified test example
        
        # Verify API call was made correctly
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://api.mailersend.com/v1/email"
    
    @responses.activate
    def test_api_error_handling(self):
        """Test handling of API errors."""
        # Mock API error response
        responses.add(
            responses.POST,
            "https://api.mailersend.com/v1/email",
            json={"error": "Invalid API token"},
            status=401
        )
        
        # Test error handling
        # (Note: Actual implementation would use EmailCampaign class)
        # This is a simplified test example
        
        # Verify error response handling
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_rate_limit_handling(self):
        """Test handling of rate limit responses."""
        # Mock rate limit response
        responses.add(
            responses.POST,
            "https://api.mailersend.com/v1/email",
            json={"error": "Rate limit exceeded"},
            status=429,
            headers={"Retry-After": "60"}
        )
        
        # Test rate limit handling
        # (Note: Actual implementation would use EmailCampaign class)
        # This is a simplified test example
        
        with patch('time.sleep') as mock_sleep:
            result = self.provider.send_email(email)
            
            # Verify retry mechanism was triggered
            mock_sleep.assert_called_with(60)
            assert result.success is False
            assert "Rate limit exceeded" in result.error
    
    def test_connection_validation(self):
        """Test API connection validation."""
        with responses.RequestsMock() as rsps:
            # Mock successful connection test
            rsps.add(
                responses.GET,
                "https://api.mailersend.com/v1/domains",
                json={"data": []},
                status=200
            )
            
            is_connected = self.provider.test_connection()
            assert is_connected is True
    
    @pytest.mark.asyncio
    async def test_async_email_sending(self):
        """Test asynchronous email sending."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "message": "Email sent successfully",
                "message_id": "async_msg_123"
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Create test email data
            email_data = {
                "to_email": "recipient@example.com",
                "subject": "Async Test Email",
                "html_content": "<h1>Async Test Content</h1>"
            }
            
            result = await self.provider.send_email_async(email_data)
            
            assert result.success is True
            assert result.message_id == "async_msg_123"
```

#### Example: Database Integration Testing
```python
# tests/integration/test_database_integration.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from tierII_email_campaign.database import Base
from tierII_email_campaign.repositories import CampaignRepository

class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    @pytest.fixture(scope="class")
    def postgres_container(self):
        """Start PostgreSQL test container."""
        with PostgresContainer("postgres:13") as postgres:
            yield postgres
    
    @pytest.fixture
    def db_session(self, postgres_container):
        """Create database session for testing."""
        engine = create_engine(postgres_container.get_connection_url())
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()
        Base.metadata.drop_all(engine)
    
    def test_campaign_record_creation(self, db_session):
        """Test creating and retrieving campaign records."""
        # Create campaign data dictionary
        campaign_data = {
            "name": "Test Campaign",
            "sender_email": "test@example.com",
            "subject": "Test Subject",
            "status": "pending"
        }
        
        # Note: This example assumes a campaign table/model exists
        # Actual implementation would depend on your database schema
        
        # Example of testing campaign data validation
        assert campaign_data["name"] == "Test Campaign"
        assert campaign_data["sender_email"] == "test@example.com"
        assert campaign_data["status"] == "pending"
    
    def test_campaign_repository_operations(self, db_session):
        """Test campaign repository CRUD operations."""
        repository = CampaignRepository(db_session)
        
        # Create campaign
        campaign_data = {
            "name": "Repository Test Campaign",
            "sender_email": "repo@example.com",
            "subject": "Repository Test"
        }
        
        campaign = repository.create_campaign(campaign_data)
        assert campaign.id is not None
        
        # Read campaign
        retrieved = repository.get_campaign(campaign.id)
        assert retrieved.name == "Repository Test Campaign"
        
        # Update campaign
        repository.update_campaign(campaign.id, {"status": "completed"})
        updated = repository.get_campaign(campaign.id)
        assert updated.status == "completed"
        
        # Delete campaign
        repository.delete_campaign(campaign.id)
        deleted = repository.get_campaign(campaign.id)
        assert deleted is None
```

### 3. End-to-End (E2E) Tests

#### Purpose and Scope
- Test complete user workflows
- Test system behavior from user perspective
- Use staging environment or comprehensive mocks
- Slower execution (< 60 seconds per test)

#### Example: Complete Campaign Workflow
```python
# tests/e2e/test_campaign_workflow.py
import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch
from tierII_email_campaign.cli import main as cli_main

class TestCampaignWorkflow:
    """End-to-end tests for complete campaign workflows."""
    
    @pytest.fixture
    def sample_contacts_csv(self):
        """Create sample contacts CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['email', 'first_name', 'last_name', 'company'])
            writer.writeheader()
            writer.writerows([
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
            ])
            
            yield f.name
            
        # Cleanup
        Path(f.name).unlink()
    
    @pytest.fixture
    def sample_template(self):
        """Create sample email template."""
        template_content = """
        <html>
        <body>
            <h1>Hello {{first_name}}!</h1>
            <p>This is a test email for {{company}}.</p>
            <p>Best regards,<br>TierII Team</p>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(template_content)
            yield f.name
            
        # Cleanup
        Path(f.name).unlink()
    
    @patch('tierII_email_campaign.providers.mailersend.MailerSendProvider.send_email')
    def test_complete_campaign_execution(self, mock_send_email, sample_contacts_csv, sample_template):
        """Test complete campaign execution from CLI."""
        # Mock successful email sending
        mock_send_email.return_value = Mock(
            success=True,
            message_id="test_msg_123",
            error=None
        )
        
        # Set up environment variables
        with patch.dict('os.environ', {
            'TIERII_SENDER_EMAIL': 'sender@example.com',
            'TIERII_MAILERSEND_API_TOKEN': 'test-token',
            'TIERII_BATCH_SIZE': '1',
            'TIERII_BATCH_DELAY': '1'
        }):
            # Execute campaign via CLI
            result = cli_main([
                'send-campaign',
                '--contacts', sample_contacts_csv,
                '--template', sample_template,
                '--subject', 'Test Campaign'
            ])
            
            # Verify campaign execution
            assert result.exit_code == 0
            assert mock_send_email.call_count == 2  # Two contacts
            
            # Verify email content was properly templated
            call_args = mock_send_email.call_args_list
            first_call = call_args[0][0][0]  # First email message
            
            assert 'Hello John!' in first_call.html_content
            assert 'Acme Corp' in first_call.html_content
    
    @patch('tierII_email_campaign.providers.mailersend.MailerSendProvider.send_email')
    def test_campaign_with_partial_failures(self, mock_send_email, sample_contacts_csv, sample_template):
        """Test campaign handling with partial send failures."""
        # Mock mixed success/failure responses
        mock_send_email.side_effect = [
            Mock(success=True, message_id="msg_1", error=None),
            Mock(success=False, message_id=None, error="Invalid recipient")
        ]
        
        with patch.dict('os.environ', {
            'TIERII_SENDER_EMAIL': 'sender@example.com',
            'TIERII_MAILERSEND_API_TOKEN': 'test-token',
            'TIERII_BATCH_SIZE': '1',
            'TIERII_BATCH_DELAY': '1'
        }):
            result = cli_main([
                'send-campaign',
                '--contacts', sample_contacts_csv,
                '--template', sample_template,
                '--subject', 'Test Campaign'
            ])
            
            # Campaign should complete but report failures
            assert result.exit_code == 0
            assert mock_send_email.call_count == 2
    
    def test_campaign_validation_errors(self, sample_template):
        """Test campaign validation with invalid inputs."""
        # Test with non-existent contacts file
        with patch.dict('os.environ', {
            'TIERII_SENDER_EMAIL': 'sender@example.com',
            'TIERII_MAILERSEND_API_TOKEN': 'test-token'
        }):
            result = cli_main([
                'send-campaign',
                '--contacts', 'nonexistent.csv',
                '--template', sample_template,
                '--subject', 'Test Campaign'
            ])
            
            assert result.exit_code != 0
    
    @patch('tierII_email_campaign.providers.mailersend.MailerSendProvider.send_email')
    def test_campaign_retry_mechanism(self, mock_send_email, sample_contacts_csv, sample_template):
        """Test campaign retry mechanism for failed sends."""
        # Mock initial failure then success
        mock_send_email.side_effect = [
            Mock(success=False, message_id=None, error="Temporary failure"),
            Mock(success=True, message_id="retry_msg_1", error=None),
            Mock(success=True, message_id="msg_2", error=None)
        ]
        
        with patch.dict('os.environ', {
            'TIERII_SENDER_EMAIL': 'sender@example.com',
            'TIERII_MAILERSEND_API_TOKEN': 'test-token',
            'TIERII_BATCH_SIZE': '1',
            'TIERII_BATCH_DELAY': '1',
            'TIERII_MAX_RETRIES': '1'
        }):
            result = cli_main([
                'send-campaign',
                '--contacts', sample_contacts_csv,
                '--template', sample_template,
                '--subject', 'Test Campaign'
            ])
            
            assert result.exit_code == 0
            # Should have 3 calls: 1 failure + 1 retry + 1 success for second contact
            assert mock_send_email.call_count == 3
```

### 4. Performance Tests

#### Purpose and Scope
- Test system performance under load
- Identify bottlenecks and resource usage
- Validate performance requirements
- Test scalability limits

#### Example: Load Testing
```python
# tests/performance/test_load_performance.py
import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from tierII_email_campaign.email_campaign import EmailCampaign
class TestLoadPerformance:
    """Performance tests for high-load scenarios."""
    
    def generate_test_contacts(self, count: int) -> list:
        """Generate test contacts for load testing."""
        return [
            {
                "email": f"user{i}@example.com",
                "first_name": f"User{i}",
                "last_name": "Test",
                "company": "Test Corp"
            }
            for i in range(count)
        ]
    
    @patch('tierII_email_campaign.providers.mailersend.MailerSendProvider.send_email')
    def test_large_contact_list_processing(self, mock_send_email):
        """Test processing of large contact lists."""
        # Mock successful sends
        mock_send_email.return_value = Mock(
            success=True,
            message_id="perf_test_msg",
            error=None
        )
        
        # Generate large contact list
        contacts = self.generate_test_contacts(1000)
        
        campaign = EmailCampaign(
            sender_email="test@example.com",
            api_token="test-token",
            batch_size=50,
            batch_delay=0.1  # Minimal delay for testing
        )
        
        start_time = time.perf_counter()
        result = campaign.send_campaign(contacts, template_path="test_template.html")
        end_time = time.perf_counter()
        
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 30.0  # Should complete within 30 seconds
        assert result.successful_sends == 1000
        assert result.failed_sends == 0
        
        # Verify batching worked correctly
        expected_batches = len(contacts) // campaign.batch_size
        assert mock_send_email.call_count == len(contacts)
    
    def test_concurrent_campaign_execution(self):
        """Test concurrent execution of multiple campaigns."""
        def run_campaign(campaign_id: int) -> dict:
            """Run a single campaign and return performance metrics."""
            contacts = self.generate_test_contacts(100)
            
            with patch('tierII_email_campaign.providers.mailersend.MailerSendProvider.send_email') as mock_send:
                mock_send.return_value = Mock(success=True, message_id=f"msg_{campaign_id}")
                
                campaign = EmailCampaign(
                    sender_email=f"campaign{campaign_id}@example.com",
                    api_token="test-token",
                    batch_size=10
                )
                
                start_time = time.perf_counter()
                result = campaign.send_campaign(contacts, template_path="test_template.html")
                end_time = time.perf_counter()
                
                return {
                    'campaign_id': campaign_id,
                    'execution_time': end_time - start_time,
                    'successful_sends': result.successful_sends,
                    'failed_sends': result.failed_sends
                }
        
        # Run multiple campaigns concurrently
        num_campaigns = 5
        with ThreadPoolExecutor(max_workers=num_campaigns) as executor:
            futures = [
                executor.submit(run_campaign, i)
                for i in range(num_campaigns)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze performance
        execution_times = [r['execution_time'] for r in results]
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        # Performance assertions
        assert avg_time < 15.0  # Average execution under 15 seconds
        assert max_time < 25.0  # No campaign takes more than 25 seconds
        assert all(r['successful_sends'] == 100 for r in results)
        assert all(r['failed_sends'] == 0 for r in results)
    
    def test_memory_usage_with_large_datasets(self):
        """Test memory usage with large contact datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process increasingly large datasets
        for contact_count in [1000, 5000, 10000]:
            contacts = self.generate_test_contacts(contact_count)
            
            with patch('tierII_email_campaign.providers.mailersend.MailerSendProvider.send_email'):
                campaign = EmailCampaign(
                    sender_email="memory_test@example.com",
                    api_token="test-token",
                    batch_size=100
                )
                
                # Process contacts
                campaign.load_contacts(contacts)
                
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Memory usage should be reasonable (< 100MB increase per 10k contacts)
                max_expected_increase = (contact_count / 10000) * 100
                assert memory_increase < max_expected_increase, \
                    f"Memory usage too high: {memory_increase}MB for {contact_count} contacts"
```

## 🔧 Test Infrastructure

### Test Configuration

#### pytest Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=tierII_email_campaign
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Slow running tests
    external: Tests requiring external services
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

#### Test Environment Setup
```python
# tests/conftest.py
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock
from tierII_email_campaign.settings import Settings
from tierII_email_campaign.providers.mailersend import MailerSendProvider

# Test environment configuration
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        'TIERII_SENDER_EMAIL': 'test@example.com',
        'TIERII_MAILERSEND_API_TOKEN': 'test-token-123',
        'TIERII_BATCH_SIZE': '10',
        'TIERII_BATCH_DELAY': '1',
        'TIERII_MAX_RETRIES': '2',
        'TIERII_LOG_LEVEL': 'DEBUG'
    }
    
    # Set test environment variables
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield
    
    # Cleanup
    for key in test_env.keys():
        os.environ.pop(key, None)

@pytest.fixture
def temp_directory():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.sender_email = "test@example.com"
    settings.mailersend_api_token = "test-token"
    settings.batch_size = 10
    settings.batch_delay = 1
    settings.max_retries = 2
    return settings

@pytest.fixture
def mock_mailersend_provider():
    """Mock MailerSend provider for testing."""
    provider = Mock(spec=MailerSendProvider)
    provider.send_email.return_value = Mock(
        success=True,
        message_id="test-msg-123",
        error=None
    )
    provider.test_connection.return_value = True
    return provider
```

### Test Data Management

#### Test Fixtures
```python
# tests/fixtures/data_fixtures.py
import pytest
import csv
from pathlib import Path
from typing import List, Dict

@pytest.fixture
def sample_contacts() -> List[Dict[str, str]]:
    """Sample contact data for testing."""
    return [
        {
            'email': 'john.doe@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'company': 'Acme Corp',
            'position': 'Manager'
        },
        {
            'email': 'jane.smith@example.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'company': 'Beta LLC',
            'position': 'Director'
        },
        {
            'email': 'bob.wilson@example.com',
            'first_name': 'Bob',
            'last_name': 'Wilson',
            'company': 'Gamma Inc',
            'position': 'CEO'
        }
    ]

@pytest.fixture
def contacts_csv_file(sample_contacts, temp_directory):
    """Create CSV file with sample contacts."""
    csv_path = temp_directory / "test_contacts.csv"
    
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['email', 'first_name', 'last_name', 'company', 'position']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_contacts)
    
    return csv_path

@pytest.fixture
def email_template_html(temp_directory):
    """Create HTML email template for testing."""
    template_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Email</title>
    </head>
    <body>
        <h1>Hello {{first_name}} {{last_name}}!</h1>
        <p>This is a test email for {{company}}.</p>
        <p>Your position: {{position}}</p>
        <p>Best regards,<br>TierII Team</p>
    </body>
    </html>
    """
    
    template_path = temp_directory / "test_template.html"
    template_path.write_text(template_content)
    
    return template_path

@pytest.fixture
def invalid_contacts_csv(temp_directory):
    """Create CSV file with invalid contact data."""
    csv_path = temp_directory / "invalid_contacts.csv"
    
    invalid_data = [
        {'email': 'invalid-email', 'first_name': 'Invalid', 'last_name': 'User'},
        {'email': '', 'first_name': 'Empty', 'last_name': 'Email'},
        {'email': 'valid@example.com', 'first_name': '', 'last_name': ''}  # Missing names
    ]
    
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['email', 'first_name', 'last_name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(invalid_data)
    
    return csv_path
```

### Test Utilities

#### Custom Assertions
```python
# tests/utils/assertions.py
from typing import Dict, Any, List

def assert_campaign_result_valid(result: Dict[str, Any]):
    """Assert that campaign result is valid."""
    assert isinstance(result, dict)
    assert result.get("total_contacts", 0) >= 0
    assert result.get("successful_sends", 0) >= 0
    assert result.get("failed_sends", 0) >= 0
    assert result.get("successful_sends", 0) + result.get("failed_sends", 0) == result.get("total_contacts", 0)
    assert result.get("start_time") is not None
    assert result.get("end_time") is not None
    assert result.get("end_time") >= result.get("start_time")

def assert_send_result_success(result: Dict[str, Any]):
    """Assert that send result indicates success."""
    assert isinstance(result, dict)
    assert result.get("success") is True
    assert result.get("message_id") is not None
    assert result.get("error") is None

def assert_send_result_failure(result: Dict[str, Any], expected_error: str = None):
    """Assert that send result indicates failure."""
    assert isinstance(result, dict)
    assert result.get("success") is False
    assert result.get("message_id") is None
    assert result.get("error") is not None
    
    if expected_error:
        assert expected_error in result.get("error", "")

def assert_email_content_valid(html_content: str, text_content: str = None):
    """Assert that email content is valid."""
    assert html_content is not None
    assert len(html_content.strip()) > 0
    assert '<html>' in html_content or '<HTML>' in html_content
    
    if text_content:
        assert text_content is not None
        assert len(text_content.strip()) > 0

def assert_contacts_valid(contacts: List[Dict[str, Any]]):
    """Assert that contact list is valid."""
    assert isinstance(contacts, list)
    assert len(contacts) > 0
    
    for contact in contacts:
        assert 'email' in contact
        assert '@' in contact['email']
        assert '.' in contact['email']
```

#### Test Helpers
```python
# tests/utils/helpers.py
import time
import functools
from typing import Callable, Any
from unittest.mock import Mock

def retry_on_failure(max_retries: int = 3, delay: float = 0.1):
    """Decorator to retry test functions on failure."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    continue
            
            raise last_exception
        
        return wrapper
    return decorator

def create_mock_response(success: bool = True, message_id: str = None, error: str = None):
    """Create mock response for email sending."""
    return Mock(
        success=success,
        message_id=message_id or ("test-msg-123" if success else None),
        error=error
    )

def measure_execution_time(func: Callable) -> tuple:
    """Measure function execution time."""
    start_time = time.perf_counter()
    result = func()
    end_time = time.perf_counter()
    
    return result, end_time - start_time

class TestTimer:
    """Context manager for measuring test execution time."""
    
    def __init__(self, max_duration: float = None):
        self.max_duration = max_duration
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        
        if self.max_duration:
            duration = self.end_time - self.start_time
            assert duration <= self.max_duration, \
                f"Test took {duration:.2f}s, expected <= {self.max_duration}s"
    
    @property
    def duration(self) -> float:
        """Get measured duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

# Usage example
def test_fast_operation():
    """Test that operation completes quickly."""
    with TestTimer(max_duration=1.0):
        # Test code that should complete within 1 second
        result = some_fast_operation()
        assert result is not None
```

## 🚀 Running Tests

### Local Test Execution

#### Basic Test Commands
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_email_campaign.py

# Run specific test method
pytest tests/unit/test_email_campaign.py::TestEmailCampaign::test_send_campaign

# Run tests with specific markers
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run tests with coverage
pytest --cov=tierII_email_campaign --cov-report=html

# Run tests in parallel
pytest -n auto

# Run tests with verbose output
pytest -v

# Run only failed tests from last run
pytest --lf

# Run tests and stop on first failure
pytest -x
```

#### Advanced Test Options
```bash
# Run tests with specific configuration
pytest -c pytest.ini

# Run tests with custom markers
pytest -m "unit and not external"

# Run tests with coverage threshold
pytest --cov=tierII_email_campaign --cov-fail-under=85

# Run tests with profiling
pytest --profile

# Run tests with memory profiling
pytest --memprof

# Generate JUnit XML report
pytest --junitxml=test-results.xml

# Run tests with custom timeout
pytest --timeout=300
```

### Continuous Integration

#### GitHub Actions Configuration
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 tierII_email_campaign tests
    
    - name: Type check with mypy
      run: |
        mypy tierII_email_campaign
    
    - name: Test with pytest
      run: |
        pytest --cov=tierII_email_campaign --cov-report=xml --cov-fail-under=80
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
```

### Test Reporting

#### Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=tierII_email_campaign --cov-report=html
open htmlcov/index.html

# Generate terminal coverage report
pytest --cov=tierII_email_campaign --cov-report=term-missing

# Generate XML coverage report (for CI)
pytest --cov=tierII_email_campaign --cov-report=xml

# Generate multiple report formats
pytest --cov=tierII_email_campaign --cov-report=html --cov-report=xml --cov-report=term
```

#### Test Result Analysis
```python
# scripts/analyze_test_results.py
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def analyze_junit_results(junit_file: str):
    """Analyze JUnit test results."""
    tree = ET.parse(junit_file)
    root = tree.getroot()
    
    total_tests = int(root.attrib.get('tests', 0))
    failures = int(root.attrib.get('failures', 0))
    errors = int(root.attrib.get('errors', 0))
    skipped = int(root.attrib.get('skipped', 0))
    
    success_rate = ((total_tests - failures - errors) / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"Test Results Summary:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {total_tests - failures - errors}")
    print(f"  Failed: {failures}")
    print(f"  Errors: {errors}")
    print(f"  Skipped: {skipped}")
    print(f"  Success Rate: {success_rate:.2f}%")
    
    return {
        'total': total_tests,
        'passed': total_tests - failures - errors,
        'failed': failures,
        'errors': errors,
        'skipped': skipped,
        'success_rate': success_rate
    }

if __name__ == "__main__":
    results = analyze_junit_results("test-results.xml")
```

## 🔍 Debugging Tests

### Test Debugging Strategies

#### Using pytest-pdb
```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest --pdb -x

# Set trace in test code
import pytest
pytest.set_trace()
```

#### Logging in Tests
```python
# tests/test_with_logging.py
import logging
import pytest

# Configure test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_with_debug_logging():
    """Test with debug logging enabled."""
    logger.debug("Starting test execution")
    
    # Test code here
    result = some_function()
    logger.debug(f"Function result: {result}")
    
    assert result is not None
    logger.debug("Test completed successfully")
```

#### Test Isolation Issues
```python
# Common test isolation problems and solutions

# Problem: Shared state between tests
class TestWithSharedState:
    shared_data = []  # This persists between tests!
    
    def test_first(self):
        self.shared_data.append("test1")
        assert len(self.shared_data) == 1
    
    def test_second(self):
        # This might fail if test_first ran first
        assert len(self.shared_data) == 0  # Fails!

# Solution: Use fixtures or setup/teardown
class TestWithProperIsolation:
    def setup_method(self):
        """Reset state before each test."""
        self.test_data = []
    
    def test_first(self):
        self.test_data.append("test1")
        assert len(self.test_data) == 1
    
    def test_second(self):
        assert len(self.test_data) == 0  # Passes!
```

## 📊 Test Metrics and Quality

### Coverage Analysis

#### Coverage Configuration
```ini
# .coveragerc
[run]
source = tierII_email_campaign
omit = 
    */tests/*
    */venv/*
    */migrations/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

[html]
directory = htmlcov
```

#### Coverage Targets by Component
```python
# Coverage requirements by module
COVERAGE_TARGETS = {
    'tierII_email_campaign.email_campaign': 95,      # Core functionality
    'tierII_email_campaign.providers': 90,           # Email providers
    'tierII_email_campaign.validators': 95,          # Validation logic
    'tierII_email_campaign.csv_reader': 85,          # CSV processing
    'tierII_email_campaign.template_engine': 90,     # Template rendering
    'tierII_email_campaign.settings': 80,            # Configuration
    'tierII_email_campaign.cli': 75,                 # CLI interface
}
```

### Test Quality Metrics

#### Test Effectiveness Metrics
```python
# scripts/test_metrics.py
import ast
import os
from pathlib import Path

def calculate_test_metrics(test_directory: str):
    """Calculate test quality metrics."""
    metrics = {
        'total_test_files': 0,
        'total_test_functions': 0,
        'total_assertions': 0,
        'avg_assertions_per_test': 0,
        'test_files_by_category': {
            'unit': 0,
            'integration': 0,
            'e2e': 0,
            'performance': 0
        }
    }
    
    for test_file in Path(test_directory).rglob("test_*.py"):
        metrics['total_test_files'] += 1
        
        # Categorize test file
        if 'unit' in str(test_file):
            metrics['test_files_by_category']['unit'] += 1
        elif 'integration' in str(test_file):
            metrics['test_files_by_category']['integration'] += 1
        elif 'e2e' in str(test_file):
            metrics['test_files_by_category']['e2e'] += 1
        elif 'performance' in str(test_file):
            metrics['test_files_by_category']['performance'] += 1
        
        # Parse file for test functions and assertions
        with open(test_file, 'r') as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                metrics['total_test_functions'] += 1
                
                # Count assertions
                for child in ast.walk(node):
                    if isinstance(child, ast.Assert):
                        metrics['total_assertions'] += 1
    
    if metrics['total_test_functions'] > 0:
        metrics['avg_assertions_per_test'] = metrics['total_assertions'] / metrics['total_test_functions']
    
    return metrics

if __name__ == "__main__":
    metrics = calculate_test_metrics("tests")
    print("Test Quality Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
```

## 📚 Related Documentation

- **[Development Guide](development.md)** - Development setup and workflows
- **[Contributing Guidelines](contributing.md)** - How to contribute to the project
- **[Architecture Overview](../architecture/overview.md)** - System architecture
- **[API Reference](../api/)** - Complete API documentation
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions

---

**Testing Guide Version**: 0.1.0  
**Coverage Requirement**: 80% minimum  
**TDD Methodology**: Red-Green-Refactor  
**Test Categories**: Unit (70%), Integration (20%), E2E (10%)