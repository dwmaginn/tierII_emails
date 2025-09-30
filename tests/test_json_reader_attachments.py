"""Comprehensive test suite for json_reader.py attachment processing functionality."""

import pytest
import os
import json
import tempfile
import base64
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Any

from src.utils.json_reader import load_email_config


class TestAttachmentProcessing:
    """Test suite for attachment processing in json_reader.py."""
    
    @pytest.fixture
    def sample_image_data(self):
        """Sample binary image data for testing."""
        # Create a minimal PNG-like binary data for testing
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
    
    @pytest.fixture
    def sample_config_with_attachments(self):
        """Sample email configuration with attachments."""
        return {
            "subject": "Test Email with Attachments",
            "body": "Hi {name},\n\nThis is a test email with attachments.\n\nBest regards,\nTest Team",
            "html": "templates/test_template.html",
            "attachments": [
                {
                    "filename": "test_logo.png",
                    "path": "templates/assets/test_logo.png",
                    "content_id": "test-logo",
                    "disposition": "inline"
                },
                {
                    "filename": "document.pdf",
                    "path": "templates/assets/document.pdf",
                    "content_id": "test-doc",
                    "disposition": "attachment"
                }
            ],
            "contacts": "data/test/testdata.csv"
        }
    
    @pytest.fixture
    def sample_config_empty_attachments(self):
        """Sample email configuration with empty attachments array."""
        return {
            "subject": "Test Email No Attachments",
            "body": "Hi {name},\n\nThis is a test email without attachments.\n\nBest regards,\nTest Team",
            "html": "templates/test_template.html",
            "attachments": [],
            "contacts": "data/test/testdata.csv"
        }
    
    @pytest.fixture
    def sample_config_no_attachments_key(self):
        """Sample email configuration without attachments key."""
        return {
            "subject": "Test Email No Attachments Key",
            "body": "Hi {name},\n\nThis is a test email without attachments key.\n\nBest regards,\nTest Team",
            "html": "templates/test_template.html",
            "contacts": "data/test/testdata.csv"
        }

    def test_load_config_with_valid_attachments(self, sample_config_with_attachments, sample_image_data):
        """Test loading configuration with valid attachments processes them correctly."""
        html_content = "<html><body><h1>Test</h1><img src='cid:test-logo'></body></html>"
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=sample_config_with_attachments):
                with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
                    # Mock file reads: first for JSON, second for HTML, then for attachments
                    mock_file.return_value.read.side_effect = [
                        html_content,  # HTML template read
                        sample_image_data,  # First attachment read
                        b'PDF content here'  # Second attachment read
                    ]
                    
                    result = load_email_config()
                    
                    # Verify processed_attachments exists and has correct structure
                    assert 'processed_attachments' in result
                    assert len(result['processed_attachments']) == 2
                    
                    # Verify first attachment (inline image)
                    first_attachment = result['processed_attachments'][0]
                    assert first_attachment['filename'] == 'test_logo.png'
                    assert first_attachment['content_id'] == 'test-logo'
                    assert first_attachment['disposition'] == 'inline'
                    assert 'content' in first_attachment
                    assert isinstance(first_attachment['content'], str)  # Base64 encoded
                    
                    # Verify second attachment (regular attachment)
                    second_attachment = result['processed_attachments'][1]
                    assert second_attachment['filename'] == 'document.pdf'
                    assert second_attachment['content_id'] == 'test-doc'
                    assert second_attachment['disposition'] == 'attachment'
                    assert 'content' in second_attachment

    def test_load_config_with_empty_attachments_array(self, sample_config_empty_attachments):
        """Test loading configuration with empty attachments array."""
        html_content = "<html><body><h1>Test</h1></body></html>"
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=sample_config_empty_attachments):
                with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
                    mock_file.return_value.read.return_value = html_content
                    
                    result = load_email_config()
                    
                    # Verify processed_attachments exists but is empty
                    assert 'processed_attachments' in result
                    assert result['processed_attachments'] == []

    def test_load_config_without_attachments_key(self, sample_config_no_attachments_key):
        """Test loading configuration without attachments key creates empty processed_attachments."""
        html_content = "<html><body><h1>Test</h1></body></html>"
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=sample_config_no_attachments_key):
                with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
                    mock_file.return_value.read.return_value = html_content
                    
                    result = load_email_config()
                    
                    # Verify processed_attachments exists but is empty
                    assert 'processed_attachments' in result
                    assert result['processed_attachments'] == []

    def test_attachment_file_not_found_handling(self, sample_config_with_attachments):
        """Test handling of missing attachment files."""
        html_content = "<html><body><h1>Test</h1></body></html>"
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=sample_config_with_attachments):
                with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
                    # Mock HTML file read success, but attachment file read failure
                    def side_effect(*args, **kwargs):
                        if 'test_template.html' in str(args[0]):
                            return mock_open(read_data=html_content).return_value
                        elif 'email_config.json' in str(args[0]):
                            return mock_open().return_value
                        else:
                            raise FileNotFoundError("Attachment file not found")
                    
                    mock_file.side_effect = side_effect
                    
                    result = load_email_config()
                    
                    # Should handle missing files gracefully
                    assert 'processed_attachments' in result
                    assert result['processed_attachments'] == []

    def test_base64_encoding_correctness(self, sample_config_with_attachments, sample_image_data):
        """Test that Base64 encoding is performed correctly."""
        html_content = "<html><body><h1>Test</h1></body></html>"
        expected_base64 = base64.b64encode(sample_image_data).decode('utf-8')
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=sample_config_with_attachments):
                with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
                    mock_file.return_value.read.side_effect = [
                        html_content,
                        sample_image_data,
                        b'PDF content'
                    ]
                    
                    result = load_email_config()
                    
                    # Verify Base64 encoding is correct
                    first_attachment = result['processed_attachments'][0]
                    assert first_attachment['content'] == expected_base64

    def test_attachment_disposition_defaults(self):
        """Test that attachment disposition defaults to 'attachment' when not specified."""
        config_with_no_disposition = {
            "subject": "Test",
            "body": "Test body",
            "html": "templates/test.html",
            "attachments": [
                {
                    "filename": "test.png",
                    "path": "templates/assets/test.png",
                    "content_id": "test-img"
                    # No disposition specified
                }
            ],
            "contacts": "data/test.csv"
        }
        
        html_content = "<html><body><h1>Test</h1></body></html>"
        sample_data = b'test data'
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=config_with_no_disposition):
                with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
                    mock_file.return_value.read.side_effect = [html_content, sample_data]
                    
                    result = load_email_config()
                    
                    # Verify default disposition is 'attachment'
                    assert result['processed_attachments'][0]['disposition'] == 'attachment'

    def test_attachment_without_content_id(self):
        """Test handling of attachments without content_id."""
        config_no_content_id = {
            "subject": "Test",
            "body": "Test body",
            "html": "templates/test.html",
            "attachments": [
                {
                    "filename": "test.png",
                    "path": "templates/assets/test.png",
                    "disposition": "inline"
                    # No content_id specified
                }
            ],
            "contacts": "data/test.csv"
        }
        
        html_content = "<html><body><h1>Test</h1></body></html>"
        sample_data = b'test data'
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=config_no_content_id):
                with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
                    mock_file.return_value.read.side_effect = [html_content, sample_data]
                    
                    result = load_email_config()
                    
                    # Verify content_id is None when not specified
                    assert result['processed_attachments'][0]['content_id'] is None

    def test_multiple_attachments_processing(self, sample_image_data):
        """Test processing multiple attachments with different types."""
        config_multiple = {
            "subject": "Test Multiple Attachments",
            "body": "Test body",
            "html": "templates/test.html",
            "attachments": [
                {
                    "filename": "logo.png",
                    "path": "templates/assets/logo.png",
                    "content_id": "logo",
                    "disposition": "inline"
                },
                {
                    "filename": "banner.jpg",
                    "path": "templates/assets/banner.jpg",
                    "content_id": "banner",
                    "disposition": "inline"
                },
                {
                    "filename": "terms.pdf",
                    "path": "templates/assets/terms.pdf",
                    "disposition": "attachment"
                }
            ],
            "contacts": "data/test.csv"
        }
        
        html_content = "<html><body><h1>Test</h1></body></html>"
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=config_multiple):
                with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
                    mock_file.return_value.read.side_effect = [
                        html_content,
                        sample_image_data,  # logo.png
                        b'JPEG data here',  # banner.jpg
                        b'PDF content here'  # terms.pdf
                    ]
                    
                    result = load_email_config()
                    
                    # Verify all attachments are processed
                    assert len(result['processed_attachments']) == 3
                    
                    # Verify each attachment has correct properties
                    attachments = result['processed_attachments']
                    assert attachments[0]['filename'] == 'logo.png'
                    assert attachments[0]['disposition'] == 'inline'
                    assert attachments[1]['filename'] == 'banner.jpg'
                    assert attachments[1]['disposition'] == 'inline'
                    assert attachments[2]['filename'] == 'terms.pdf'
                    assert attachments[2]['disposition'] == 'attachment'

    def test_backward_compatibility_existing_functionality(self, sample_config_no_attachments_key):
        """Test that existing functionality without attachments continues to work."""
        html_content = "<html><body><h1>Hi {name}</h1></body></html>"
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=sample_config_no_attachments_key):
                with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
                    mock_file.return_value.read.return_value = html_content
                    
                    result = load_email_config()
                    
                    # Verify all existing functionality still works
                    assert result['subject'] == sample_config_no_attachments_key['subject']
                    assert result['body'] == sample_config_no_attachments_key['body']
                    assert result['html_content'] == html_content
                    assert result['contacts'] == sample_config_no_attachments_key['contacts']
                    
                    # Verify new functionality doesn't break existing behavior
                    assert 'processed_attachments' in result
                    assert result['processed_attachments'] == []