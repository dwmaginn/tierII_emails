"""Pytest configuration and shared fixtures for email campaign tests."""

import os
import json
import tempfile
import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing contact parsing."""
    return """License Number,License Type,License Type Code,License Status,License Status Code,Issued Date,Effective Date,Expiration Date,Application Number,Entity Name,Address Line 1,Address Line 2,City,State,Zip Code,County,Region,Business Website,Operational Status,Business Purpose,Tier Type,Processor Type,Primary Contact Name,Email
TEST-CULT-25-000001,Adult-Use Cultivation License,OCMCULT,Active,LICACT,1/1/2025 0:00,1/1/2025 0:00,1/1/2027 0:00,TESTCULT-2024-000001,Green Thumb Cultivation LLC,123 Main Street,,Rochester,NY,14623,Monroe,Finger Lakes,www.greenthumb.com,Active,Adult-Use Cultivation,INDOOR,N/A,John Smith,john@greenthumb.com
TEST-PROC-25-000002,Adult-Use Processor License,OCMPROC,Active,LICACT,1/2/2025 0:00,1/2/2025 0:00,1/2/2027 0:00,TESTPROC-2024-000002,Spider Processing Inc,456 Spider Lane,,Buffalo,NY,14201,Erie,Western NY,www.spiderprocessing.com,Active,Adult-Use Processing,,Type 1 - Extracting,David Spider,david@spider.com
TEST-MICR-25-000003,Adult-Use Microbusiness License,OCMMICR,Active,LICACT,1/3/2025 0:00,1/3/2025 0:00,1/3/2027 0:00,TESTMICR-2024-000003,RIT Cannabis Research LLC,789 University Ave,,Rochester,NY,14623,Monroe,Finger Lakes,www.ritcannabis.edu,Non-Operational,"Adult-Use Cultivation, Adult-Use Processing",MICROBUS_COMBINATION,"Infusing and Blending; and Packaging, Labeling and Branding",Luke Edwards,luke@rit.edu"""


@pytest.fixture
def sample_invalid_csv_data():
    """Sample CSV data with invalid entries for testing error handling."""
    return """License Number,License Type,License Type Code,License Status,License Status Code,Issued Date,Effective Date,Expiration Date,Application Number,Entity Name,Address Line 1,Address Line 2,City,State,Zip Code,County,Region,Business Website,Operational Status,Business Purpose,Tier Type,Processor Type,Primary Contact Name,Email
TEST-INVALID-001,Test License,TEST,Active,LICACT,1/1/2025,1/1/2025,1/1/2027,TEST-001,Invalid Email Co,123 Test St,,Test City,NY,12345,Test County,Test Region,www.test.com,Active,Testing,,N/A,Invalid Contact,invalid-email
TEST-INVALID-002,Test License,TEST,Active,LICACT,1/1/2025,1/1/2025,1/1/2027,TEST-002,No Email Co,456 Test Ave,,Test City,NY,12345,Test County,Test Region,www.test.com,Active,Testing,,N/A,No Email Contact,"""


@pytest.fixture
def sample_email_config():
    """Sample email configuration for testing."""
    return {
        "subject": "Test Email Subject",
        "body": "Hi {name},\n\nThis is a test email.\n\nBest regards,\nTest Team",
        "html": "templates/test_template.html",
        "html_content": "<html><body><h1>Hi {name}</h1><p>This is a test email.</p></body></html>",
        "attachments": []
    }


@pytest.fixture
def sample_rate_config():
    """Sample rate limiting configuration for testing."""
    return {
        "batch_size": 5,
        "cooldown": 30,
        "individual_cooldown": 3
    }


@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(sample_csv_data)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_invalid_csv_file(sample_invalid_csv_data):
    """Create a temporary CSV file with invalid data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(sample_invalid_csv_data)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_email_config_file(sample_email_config):
    """Create a temporary email config JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(sample_email_config, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_html_template():
    """Create a temporary HTML template file."""
    html_content = "<html><body><h1>Hi {name}</h1><p>This is a test email template.</p></body></html>"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_mailersend_client():
    """Mock MailerSend client for testing email functionality."""
    mock_client = Mock()
    mock_emails = Mock()
    mock_client.emails = mock_emails
    
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 202
    mock_response.text = "Email queued successfully"
    mock_emails.send.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_mailersend_failed_client():
    """Mock MailerSend client that returns failed responses."""
    mock_client = Mock()
    mock_emails = Mock()
    mock_client.emails = mock_emails
    
    # Mock failed response
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request: Invalid email format"
    mock_emails.send.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing."""
    env_vars = {
        'TIERII_MAILERSEND_API_TOKEN': 'test_api_token_12345',
        'TIERII_SENDER_EMAIL': 'test@example.com'
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_contacts():
    """Sample parsed contacts for testing."""
    return [
        {
            "License Number": "TEST-CULT-25-000001",
            "License Type": "Adult-Use Cultivation License",
            "License Type Code": "OCMCULT",
            "License Status": "Active",
            "License Status Code": "LICACT",
            "Issued Date": "1/1/2025 0:00",
            "Effective Date": "1/1/2025 0:00",
            "Expiration Date": "1/1/2027 0:00",
            "Application Number": "TESTCULT-2024-000001",
            "Entity Name": "Green Thumb Cultivation LLC",
            "Address Line 1": "123 Main Street",
            "Address Line 2": "",
            "City": "Rochester",
            "State": "NY",
            "Zip Code": "14623",
            "County": "Monroe",
            "Region": "Finger Lakes",
            "Business Website": "www.greenthumb.com",
            "Operational Status": "Active",
            "Business Purpose": "Adult-Use Cultivation",
            "Tier Type": "INDOOR",
            "Processor Type": "N/A",
            "Primary Contact Name": "John Smith",
            "Email": "john@greenthumb.com",
            "first_name": "John"
        },
        {
            "License Number": "TEST-PROC-25-000002",
            "License Type": "Adult-Use Processor License",
            "License Type Code": "OCMPROC",
            "License Status": "Active",
            "License Status Code": "LICACT",
            "Issued Date": "1/2/2025 0:00",
            "Effective Date": "1/2/2025 0:00",
            "Expiration Date": "1/2/2027 0:00",
            "Application Number": "TESTPROC-2024-000002",
            "Entity Name": "Spider Processing Inc",
            "Address Line 1": "456 Spider Lane",
            "Address Line 2": "",
            "City": "Buffalo",
            "State": "NY",
            "Zip Code": "14201",
            "County": "Erie",
            "Region": "Western NY",
            "Business Website": "www.spiderprocessing.com",
            "Operational Status": "Active",
            "Business Purpose": "Adult-Use Processing",
            "Tier Type": "",
            "Processor Type": "Type 1 - Extracting",
            "Primary Contact Name": "David Spider",
            "Email": "david@spider.com",
            "first_name": "David"
        }
    ]


@pytest.fixture
def temp_logs_dir():
    """Create a temporary logs directory for testing."""
    temp_dir = tempfile.mkdtemp()
    logs_dir = os.path.join(temp_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    yield logs_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def mock_sleep():
    """Mock time.sleep to speed up tests."""
    with patch('time.sleep'):
        yield


@pytest.fixture(autouse=True)
def mock_webbrowser():
    """Mock webbrowser.open to prevent opening browsers during tests."""
    with patch('webbrowser.open'):
        yield