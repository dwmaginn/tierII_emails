"""Comprehensive test suite for csv_reader.py contact parsing functionality."""

import pytest
import os
import tempfile
import csv
from unittest.mock import patch, mock_open

from src.utils.csv_reader import (
    parse_contacts_from_csv,
    load_default_contacts,
    validate_contacts,
    ContactParseError,
    _extract_first_name,
    _is_valid_email,
    _parse_contact_row
)


class TestExtractFirstName:
    """Test suite for _extract_first_name function."""
    
    def test_extract_first_name_single_name(self):
        """Test extracting first name from single name."""
        assert _extract_first_name("John") == "John"
    
    def test_extract_first_name_full_name(self):
        """Test extracting first name from full name."""
        assert _extract_first_name("John Doe") == "John"
        assert _extract_first_name("Jane Mary Smith") == "Jane"
    
    def test_extract_first_name_with_title(self):
        """Test extracting first name with title prefix."""
        assert _extract_first_name("Dr. John Doe") == "John"
        assert _extract_first_name("Mr. Smith Johnson") == "Smith"  
        assert _extract_first_name("Mrs. Jane Doe") == "Jane"
    
    def test_extract_first_name_empty_string(self):
        """Test extracting first name from empty string."""
        assert _extract_first_name("") == ""
    
    def test_extract_first_name_whitespace_only(self):
        """Test extracting first name from whitespace-only string."""
        assert _extract_first_name("   ") == ""
        assert _extract_first_name("\t\n") == ""
    
    def test_extract_first_name_leading_trailing_spaces(self):
        """Test extracting first name with leading/trailing spaces."""
        assert _extract_first_name("  John  ") == "John"
        assert _extract_first_name("\tJane Doe\n") == "Jane"
    
    def test_extract_first_name_special_characters(self):
        """Test extracting first name with special characters."""
        assert _extract_first_name("John-Paul Smith") == "Johnpaul"
        assert _extract_first_name("Mary.Jane Doe") == "Maryjane"
        assert _extract_first_name("O'Connor") == "Oconnor"


class TestIsValidEmail:
    """Test suite for _is_valid_email function."""
    
    def test_is_valid_email_standard_format(self):
        """Test valid email formats."""
        assert _is_valid_email("test@example.com") is True
        assert _is_valid_email("user.name@domain.org") is True
        assert _is_valid_email("first.last+tag@subdomain.example.co.uk") is True
        assert _is_valid_email("user123@test-domain.com") is True
    
    def test_is_valid_email_invalid_format(self):
        """Test email validation with invalid formats."""
        assert _is_valid_email("invalid.email") == False
        assert _is_valid_email("user@") == False
        assert _is_valid_email("@domain.com") == False
        assert _is_valid_email("user@domain") == False
        assert _is_valid_email("user space@domain.com") == False
    
    def test_is_valid_email_edge_cases(self):
        """Test edge cases for email validation."""
        assert _is_valid_email("") is False
        assert _is_valid_email("   ") is False
        assert _is_valid_email("user@domain.c") is False  # TLD too short
        assert _is_valid_email("user@domain.toolong") is True  # Should be valid


class TestParseContactRow:
    """Test suite for _parse_contact_row function."""
    
    def test_parse_contact_row_valid_data(self):
        """Test parsing a valid contact row."""
        row = {
            "Email": "john@example.com",
            "Primary Contact Name": "John Doe",
            "Entity Name": "Test Company",
            "License Number": "12345",
            "Address Line 1": "123 Main St",
            "City": "Anytown",
            "State": "CA",
            "Zip Code": "12345"
        }
        
        contact = _parse_contact_row(row)
        assert contact is not None
        assert contact["Email"] == "john@example.com"
        assert contact["Primary Contact Name"] == "John Doe"
        assert contact["first_name"] == "John"
        assert contact["Entity Name"] == "Test Company"
        assert contact["License Number"] == "12345"
    
    def test_parse_contact_row_invalid_email(self):
        """Test parsing row with invalid email."""
        row = {
            "Email": "invalid-email",
            "Primary Contact Name": "John Doe"
        }
        
        contact = _parse_contact_row(row)
        assert contact is None
    
    def test_parse_contact_row_missing_email(self):
        """Test parsing row with missing email."""
        row = {
            "Primary Contact Name": "John Doe"
        }
        
        contact = _parse_contact_row(row)
        assert contact is None
    
    def test_parse_contact_row_empty_email(self):
        """Test parsing row with empty email."""
        row = {
            "Email": "",
            "Primary Contact Name": "John Doe"
        }
        
        contact = _parse_contact_row(row)
        assert contact is None


class TestValidateContacts:
    """Test suite for validate_contacts function."""
    
    def test_validate_contacts_valid_list(self):
        """Test validating a list of valid contacts."""
        contacts = [
            {"email": "john@example.com", "first_name": "John"},
            {"email": "jane@example.com", "first_name": "Jane"}
        ]
        
        errors = validate_contacts(contacts)
        assert errors == []
    
    def test_validate_contacts_missing_email(self):
        """Test validating contacts with missing email."""
        contacts = [
            {"first_name": "John"}
        ]
        
        errors = validate_contacts(contacts)
        assert len(errors) == 1
        assert "Missing email address" in errors[0]
    
    def test_validate_contacts_invalid_email(self):
        """Test validating contacts with invalid email."""
        contacts = [
            {"email": "invalid-email", "first_name": "John"}
        ]
        
        errors = validate_contacts(contacts)
        assert len(errors) == 1
        assert "Invalid email format" in errors[0]
    
    def test_validate_contacts_missing_name(self):
        """Test validating contacts with missing name fields."""
        contacts = [
            {"email": "john@example.com"}
        ]
        
        errors = validate_contacts(contacts)
        assert len(errors) == 1
        assert "Missing both first name and contact name" in errors[0]


class TestParseContactsFromCsv:
    """Test suite for parse_contacts_from_csv function."""
    
    def test_parse_contacts_from_csv_valid_file(self):
        """Test parsing valid CSV file."""
        csv_content = """Email,Primary Contact Name
john@example.com,John Doe
jane@example.com,Jane Smith"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            temp_file_name = f.name
            
        try:
            contacts = parse_contacts_from_csv(temp_file_name)
            assert len(contacts) == 2
            assert contacts[0]["Email"] == "john@example.com"
            assert contacts[0]["first_name"] == "John"
            assert contacts[1]["Email"] == "jane@example.com"
            assert contacts[1]["first_name"] == "Jane"
        finally:
            os.unlink(temp_file_name)
    
    def test_parse_contacts_from_csv_file_not_found(self):
        """Test parsing non-existent CSV file."""
        with pytest.raises(FileNotFoundError):
            parse_contacts_from_csv("non_existent_file.csv")
    
    def test_parse_contacts_from_csv_invalid_contacts(self):
        """Test parsing CSV with invalid contacts."""
        csv_content = """Email,Primary Contact Name
invalid-email,John Doe
jane@example.com,Jane Smith"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            temp_file_name = f.name
            
        try:
            contacts = parse_contacts_from_csv(temp_file_name)
            # Only valid contacts should be returned
            assert len(contacts) == 1
            assert contacts[0]["Email"] == "jane@example.com"
        finally:
            os.unlink(temp_file_name)
    
    def test_parse_contacts_from_csv_empty_file(self):
        """Test parsing empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("")
            f.flush()
            temp_file_name = f.name
            
        try:
            contacts = parse_contacts_from_csv(temp_file_name)
            assert contacts == []
        finally:
            os.unlink(temp_file_name)


class TestLoadDefaultContacts:
    """Test suite for load_default_contacts function."""
    
    @patch('src.utils.csv_reader.parse_contacts_from_csv')
    def test_load_default_contacts_success(self, mock_parse_contacts):
        """Test successful loading of default contacts."""
        mock_contacts = [
            {"email": "test@example.com", "first_name": "Test"}
        ]
        mock_parse_contacts.return_value = mock_contacts
        
        contacts = load_default_contacts()
        assert contacts == mock_contacts
        
        # Verify the correct path was used
        expected_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "src", "utils", "..", "..", "data", "contacts", 
            "tier_i_tier_ii_emails_verified.csv"
        )
        mock_parse_contacts.assert_called_once()
    
    @patch('src.utils.csv_reader.parse_contacts_from_csv')
    def test_load_default_contacts_file_not_found(self, mock_parse_contacts):
        """Test loading default contacts when file not found."""
        mock_parse_contacts.side_effect = FileNotFoundError("File not found")
        
        with pytest.raises(FileNotFoundError):
            load_default_contacts()
    
    @patch('src.utils.csv_reader.parse_contacts_from_csv')
    def test_load_default_contacts_parse_error(self, mock_parse_contacts):
        """Test loading default contacts with parse error."""
        mock_parse_contacts.side_effect = ContactParseError("Parse error")
        
        with pytest.raises(ContactParseError):
            load_default_contacts()


class TestContactParseError:
    """Test suite for ContactParseError exception."""
    
    def test_contact_parse_error_creation(self):
        """Test creating ContactParseError with message."""
        error_message = "Test error message"
        error = ContactParseError(error_message)
        
        assert str(error) == error_message
        assert isinstance(error, Exception)
    
    def test_contact_parse_error_inheritance(self):
        """Test ContactParseError inheritance."""
        error = ContactParseError("Test")
        assert isinstance(error, Exception)


class TestCsvReaderIntegration:
    """Integration tests for csv_reader module."""
    
    def test_full_csv_processing_workflow(self):
        """Test complete CSV processing workflow."""
        csv_content = """Email,Primary Contact Name,Entity Name,License Number
john@example.com,John Doe,Test Company,12345
jane@example.com,Jane Smith,Another Company,67890
invalid-email,Bad Contact,Bad Company,11111"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            temp_file_name = f.name
            
        try:
            # Parse contacts
            contacts = parse_contacts_from_csv(temp_file_name)
            assert len(contacts) == 2  # Only valid contacts
            
            # Validate contacts
            errors = validate_contacts(contacts)
            assert len(errors) == 0  # No validation errors for valid contacts
            
            # Check contact structure
            for contact in contacts:
                assert "Email" in contact
                assert "first_name" in contact
                assert "Primary Contact Name" in contact
                assert _is_valid_email(contact["Email"])
                
        finally:
            os.unlink(temp_file_name)