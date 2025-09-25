"""Unit tests for CSV reader utilities."""

import csv
import os
import tempfile
import pytest
from unittest.mock import patch, mock_open

from src.utils.csv_reader import load_contacts, validate_contact_data


class TestLoadContacts:
    """Test cases for load_contacts function."""
    
    def test_load_contacts_with_valid_file(self):
        """Test loading contacts from a valid CSV file."""
        # Create a temporary CSV file
        test_data = [
            ['email', 'name', 'company'],
            ['test@example.com', 'John Doe', 'Test Corp'],
            ['jane@example.com', 'Jane Smith', 'Example Inc']
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as temp_file:
            writer = csv.writer(temp_file)
            writer.writerows(test_data)
            temp_file_path = temp_file.name
        
        try:
            contacts = load_contacts(temp_file_path)
            
            assert len(contacts) == 2
            assert contacts[0]['email'] == 'test@example.com'
            assert contacts[0]['name'] == 'John Doe'
            assert contacts[0]['company'] == 'Test Corp'
            assert contacts[1]['email'] == 'jane@example.com'
            assert contacts[1]['name'] == 'Jane Smith'
            assert contacts[1]['company'] == 'Example Inc'
        finally:
            os.unlink(temp_file_path)
    
    def test_load_contacts_with_default_path(self):
        """Test loading contacts with default path."""
        # Mock the default test data file
        mock_data = "email,name\ntest@example.com,Test User\n"
        
        with patch('builtins.open', mock_open(read_data=mock_data)):
            with patch('os.path.exists', return_value=True):
                contacts = load_contacts()
                
                assert len(contacts) == 1
                assert contacts[0]['email'] == 'test@example.com'
                assert contacts[0]['name'] == 'Test User'
    
    def test_load_contacts_file_not_found(self):
        """Test FileNotFoundError when CSV file doesn't exist."""
        non_existent_path = '/path/to/nonexistent/file.csv'
        
        with pytest.raises(FileNotFoundError) as exc_info:
            load_contacts(non_existent_path)
        
        assert f"CSV file not found: {non_existent_path}" in str(exc_info.value)
    
    def test_load_contacts_malformed_csv(self):
        """Test ValueError when CSV file is malformed."""
        # Create a temporary file with malformed CSV content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_file.write("malformed,csv\ndata\nwith,inconsistent,columns")
            temp_file_path = temp_file.name
        
        try:
            # Mock csv.DictReader to raise an exception
            with patch('csv.DictReader') as mock_reader:
                mock_reader.side_effect = Exception("CSV parsing error")
                
                with pytest.raises(ValueError) as exc_info:
                    load_contacts(temp_file_path)
                
                assert f"Error reading CSV file {temp_file_path}" in str(exc_info.value)
                assert "CSV parsing error" in str(exc_info.value)
        finally:
            os.unlink(temp_file_path)
    
    def test_load_contacts_empty_file(self):
        """Test loading contacts from an empty CSV file."""
        # Create an empty CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(['email', 'name'])  # Header only
            temp_file_path = temp_file.name
        
        try:
            contacts = load_contacts(temp_file_path)
            assert len(contacts) == 0
        finally:
            os.unlink(temp_file_path)
    
    def test_load_contacts_with_unicode_content(self):
        """Test loading contacts with unicode characters."""
        test_data = [
            ['email', 'name'],
            ['test@example.com', 'José García'],
            ['unicode@test.com', '测试用户']
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as temp_file:
            writer = csv.writer(temp_file)
            writer.writerows(test_data)
            temp_file_path = temp_file.name
        
        try:
            contacts = load_contacts(temp_file_path)
            
            assert len(contacts) == 2
            assert contacts[0]['name'] == 'José García'
            assert contacts[1]['name'] == '测试用户'
        finally:
            os.unlink(temp_file_path)


class TestValidateContactData:
    """Test cases for validate_contact_data function."""
    
    def test_validate_contact_data_valid_contacts(self):
        """Test validation with valid contact data."""
        contacts = [
            {'email': 'test@example.com', 'name': 'John Doe'},
            {'email': 'jane@example.com', 'name': 'Jane Smith'},
            {'email': 'bob@test.com', 'company': 'Test Corp'}
        ]
        
        result = validate_contact_data(contacts)
        assert result is True
    
    def test_validate_contact_data_missing_email_field(self):
        """Test validation with missing email field."""
        contacts = [
            {'name': 'John Doe', 'company': 'Test Corp'},
            {'email': 'jane@example.com', 'name': 'Jane Smith'}
        ]
        
        result = validate_contact_data(contacts)
        assert result is False
    
    def test_validate_contact_data_empty_email_field(self):
        """Test validation with empty email field."""
        contacts = [
            {'email': '', 'name': 'John Doe'},
            {'email': 'jane@example.com', 'name': 'Jane Smith'}
        ]
        
        result = validate_contact_data(contacts)
        assert result is False
    
    def test_validate_contact_data_none_email_field(self):
        """Test validation with None email field."""
        contacts = [
            {'email': None, 'name': 'John Doe'},
            {'email': 'jane@example.com', 'name': 'Jane Smith'}
        ]
        
        result = validate_contact_data(contacts)
        assert result is False
    
    def test_validate_contact_data_empty_list(self):
        """Test validation with empty contact list."""
        contacts = []
        
        result = validate_contact_data(contacts)
        assert result is True
    
    def test_validate_contact_data_single_valid_contact(self):
        """Test validation with single valid contact."""
        contacts = [
            {'email': 'test@example.com', 'name': 'Test User'}
        ]
        
        result = validate_contact_data(contacts)
        assert result is True
    
    def test_validate_contact_data_single_invalid_contact(self):
        """Test validation with single invalid contact."""
        contacts = [
            {'name': 'Test User', 'company': 'Test Corp'}
        ]
        
        result = validate_contact_data(contacts)
        assert result is False