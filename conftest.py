"""Shared pytest fixtures and configuration for email campaign tests."""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import csv

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


@pytest.fixture
def mock_config():
    """Mock configuration values for testing."""
    return {
        'SENDER_EMAIL': 'test@example.com',
        'SMTP_SERVER': 'smtp.test.com',
        'SMTP_PORT': 587,
        'BATCH_SIZE': 5,
        'DELAY_MINUTES': 1,
        'TENANT_ID': 'test-tenant-id',
        'CLIENT_ID': 'test-client-id',
        'CLIENT_SECRET': 'test-client-secret'
    }


@pytest.fixture
def mock_oauth_response():
    """Mock OAuth token response."""
    return {
        'access_token': 'mock_access_token_12345',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': 'https://outlook.office365.com/.default'
    }


@pytest.fixture
def sample_contacts():
    """Sample contact data for testing."""
    return [
        {
            'email': 'john.doe@example.com',
            'first_name': 'John',
            'contact_name': 'John Doe'
        },
        {
            'email': 'jane.smith@test.com',
            'first_name': 'Jane',
            'contact_name': 'Dr. Jane Smith'
        },
        {
            'email': 'bob.wilson@company.org',
            'first_name': 'Bob',
            'contact_name': 'Mr. Bob Wilson'
        },
        {
            'email': 'invalid-email',
            'first_name': 'there',
            'contact_name': ''
        }
    ]


@pytest.fixture
def sample_csv_data():
    """Sample CSV data matching the expected format."""
    return [
        {
            'License Number': 'LIC001',
            'License Type': 'Adult-Use Conditional Cultivator',
            'License Type Code': 'AUCC',
            'License Status': 'Active',
            'License Status Code': 'A',
            'Issued Date': '2023-01-15',
            'Effective Date': '2023-01-15',
            'Expiration Date': '2025-01-15',
            'Application Number': 'APP001',
            'Entity Name': 'Test Cannabis Co',
            'Address Line 1': '123 Main St',
            'Address Line 2': 'Suite 100',
            'City': 'New York',
            'State': 'NY',
            'Zip Code': '10001',
            'County': 'New York',
            'Region': 'NYC',
            'Business Website': 'https://testcannabis.com',
            'Operational Status': 'Operational',
            'Business Purpose': 'Cultivation',
            'Tier Type': 'Tier I',
            'Processor Type': 'Primary',
            'Primary Contact Name': 'John Doe',
            'Email': 'john.doe@testcannabis.com'
        },
        {
            'License Number': 'LIC002',
            'License Type': 'Adult-Use Conditional Processor',
            'License Type Code': 'AUCP',
            'License Status': 'Active',
            'License Status Code': 'A',
            'Issued Date': '2023-02-01',
            'Effective Date': '2023-02-01',
            'Expiration Date': '2025-02-01',
            'Application Number': 'APP002',
            'Entity Name': 'Green Processing LLC',
            'Address Line 1': '456 Oak Ave',
            'Address Line 2': '',
            'City': 'Buffalo',
            'State': 'NY',
            'Zip Code': '14201',
            'County': 'Erie',
            'Region': 'Western NY',
            'Business Website': '',
            'Operational Status': 'Operational',
            'Business Purpose': 'Processing',
            'Tier Type': 'Tier II',
            'Processor Type': 'Secondary',
            'Primary Contact Name': 'Dr. Jane Smith',
            'Email': 'jane.smith@greenprocessing.com'
        },
        {
            'License Number': 'LIC003',
            'License Type': 'Adult-Use Conditional Retailer',
            'License Type Code': 'AUCR',
            'License Status': 'Pending',
            'License Status Code': 'P',
            'Issued Date': '2023-03-10',
            'Effective Date': '2023-03-10',
            'Expiration Date': '2025-03-10',
            'Application Number': 'APP003',
            'Entity Name': 'Cannabis Retail Store',
            'Address Line 1': '789 Pine St',
            'Address Line 2': 'Floor 2',
            'City': 'Albany',
            'State': 'NY',
            'Zip Code': '12201',
            'County': 'Albany',
            'Region': 'Capital Region',
            'Business Website': 'https://cannabisretail.com',
            'Operational Status': 'Pre-Operational',
            'Business Purpose': 'Retail',
            'Tier Type': 'Tier I',
            'Processor Type': '',
            'Primary Contact Name': '',
            'Email': ''
        }
    ]


@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        if sample_csv_data:
            fieldnames = sample_csv_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_csv_data)
        
        temp_file_path = f.name
    
    yield temp_file_path
    
    # Cleanup
    try:
        os.unlink(temp_file_path)
    except OSError:
        pass


@pytest.fixture
def mock_smtp_server():
    """Mock SMTP server for email testing."""
    mock_server = MagicMock()
    mock_server.starttls.return_value = None
    mock_server.docmd.return_value = (235, b'Authentication successful')
    mock_server.sendmail.return_value = {}
    mock_server.quit.return_value = None
    return mock_server


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for OAuth token requests."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        'access_token': 'mock_access_token_12345',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': 'https://outlook.office365.com/.default'
    }
    return mock_response


@pytest.fixture
def oauth_token_manager():
    """Create an OAuthTokenManager instance for testing."""
    # Import here to avoid circular imports
    from src.email_campaign import OAuthTokenManager
    return OAuthTokenManager()


@pytest.fixture(autouse=True)
def patch_config_import():
    """Automatically patch config imports in all tests."""
    mock_config_values = {
        'SENDER_EMAIL': 'test@example.com',
        'SMTP_SERVER': 'smtp.test.com',
        'SMTP_PORT': 587,
        'BATCH_SIZE': 5,
        'DELAY_MINUTES': 1,
        'TENANT_ID': 'test-tenant-id',
        'CLIENT_ID': 'test-client-id',
        'CLIENT_SECRET': 'test-client-secret',
        'SUBJECT': 'Test Subject'
    }
    
    with patch.dict('sys.modules', {'config': Mock(**mock_config_values)}):
        yield


@pytest.fixture
def freeze_time():
    """Fixture to freeze time for consistent testing."""
    frozen_time = datetime(2023, 6, 15, 12, 0, 0)
    with patch('src.email_campaign.datetime') as mock_datetime:
        mock_datetime.now.return_value = frozen_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield frozen_time