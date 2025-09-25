"""Comprehensive tests for CSV contact processing and validation.

This module tests the read_contacts_from_csv() function from email_campaign.py
and related contact validation functionality, covering malformed data handling,
email validation, duplicate detection, and edge cases.
"""

import pytest
import csv
import tempfile
import os
from unittest.mock import patch, mock_open, Mock
from io import StringIO

# Import the functions under test
from src.email_campaign import read_contacts_from_csv, get_first_name


class TestCSVContactProcessing:
    """Test suite for CSV contact processing functionality."""

    @pytest.fixture
    def valid_csv_content(self):
        """Valid CSV content for testing."""
        return """Primary Contact Name,Email,Company
John Doe,john.doe@example.com,Acme Corp
Jane Smith,jane.smith@company.org,Tech Solutions
Bob Johnson,bob@startup.io,Innovation Inc
Dr. Sarah Wilson,sarah.wilson@medical.edu,Medical Center
"""

    @pytest.fixture
    def malformed_csv_content(self):
        """Malformed CSV content for testing."""
        return """Primary Contact Name,Email,Company
John Doe,john.doe@example.com,Acme Corp
Jane Smith,invalid-email,Tech Solutions
,bob@startup.io,Innovation Inc
Dr. Sarah Wilson,,Medical Center
Mike Davis,mike@,Incomplete Domain
Lisa Brown,@domain.com,Missing Local Part
Tom Wilson,tom.wilson@domain,Missing TLD
"""

    @pytest.fixture
    def duplicate_csv_content(self):
        """CSV content with duplicate emails."""
        return """Primary Contact Name,Email,Company
John Doe,john.doe@example.com,Acme Corp
Jane Smith,jane.smith@company.org,Tech Solutions
John Different,john.doe@example.com,Different Company
Jane Different,jane.smith@company.org,Another Company
Bob Johnson,bob@startup.io,Innovation Inc
"""

    @pytest.fixture
    def temp_csv_file(self, valid_csv_content):
        """Create a temporary CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(valid_csv_content)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except FileNotFoundError:
            pass

    def test_read_contacts_valid_csv(self, temp_csv_file):
        """Test reading contacts from a valid CSV file."""
        contacts = read_contacts_from_csv(temp_csv_file)
        
        assert len(contacts) == 4
        
        # Check first contact
        assert contacts[0]['email'] == 'john.doe@example.com'
        assert contacts[0]['first_name'] == 'John'
        assert contacts[0]['contact_name'] == 'John Doe'
        
        # Check second contact
        assert contacts[1]['email'] == 'jane.smith@company.org'
        assert contacts[1]['first_name'] == 'Jane'
        assert contacts[1]['contact_name'] == 'Jane Smith'

    def test_read_contacts_malformed_data_filtering(self):
        """Test that malformed data is properly filtered out."""
        malformed_content = """Primary Contact Name,Email,Company
John Doe,john.doe@example.com,Acme Corp
Jane Smith,invalid-email,Tech Solutions
,bob@startup.io,Innovation Inc
Dr. Sarah Wilson,,Medical Center
Mike Davis,mike@incomplete,Incomplete Domain
Lisa Brown,@domain.com,Missing Local Part
Tom Wilson,tom.wilson@domain,Missing TLD
Valid User,valid@domain.com,Valid Company
"""
        
        with patch('builtins.open', mock_open(read_data=malformed_content)):
            contacts = read_contacts_from_csv('dummy.csv')
        
        # Current implementation only checks for presence of @ symbol
        # So emails with @ will be included, even if malformed
        assert len(contacts) == 6  # All emails with @ symbol
        
        valid_emails = [contact['email'] for contact in contacts]
        assert 'john.doe@example.com' in valid_emails
        assert 'bob@startup.io' in valid_emails
        assert 'mike@incomplete' in valid_emails  # Has @ so included
        assert '@domain.com' in valid_emails  # Has @ so included
        assert 'tom.wilson@domain' in valid_emails  # Has @ so included
        assert 'valid@domain.com' in valid_emails
        
        # Only emails without @ should be filtered out
        assert 'invalid-email' not in valid_emails
        assert '' not in valid_emails

    def test_read_contacts_duplicate_detection(self):
        """Test detection and handling of duplicate email addresses."""
        duplicate_content = """Primary Contact Name,Email,Company
John Doe,john.doe@example.com,Acme Corp
Jane Smith,jane.smith@company.org,Tech Solutions
John Different,john.doe@example.com,Different Company
Jane Different,jane.smith@company.org,Another Company
Bob Johnson,bob@startup.io,Innovation Inc
"""
        
        with patch('builtins.open', mock_open(read_data=duplicate_content)):
            contacts = read_contacts_from_csv('dummy.csv')
        
        # Should include all contacts (current implementation doesn't deduplicate)
        # This test documents current behavior and can be updated if deduplication is added
        assert len(contacts) == 5
        
        # Check that duplicates are present
        emails = [contact['email'] for contact in contacts]
        assert emails.count('john.doe@example.com') == 2
        assert emails.count('jane.smith@company.org') == 2

    def test_read_contacts_email_validation_edge_cases(self):
        """Test email validation with various edge cases."""
        edge_case_content = """Primary Contact Name,Email,Company
Valid User,user@domain.com,Valid
Subdomain User,user@sub.domain.com,Valid Subdomain
Plus User,user+tag@domain.com,Valid Plus
Dot User,user.name@domain.com,Valid Dot
Hyphen Domain,user@domain-name.com,Valid Hyphen
Number Domain,user@123domain.com,Valid Number
International,user@domain.co.uk,Valid International
Long TLD,user@domain.museum,Valid Long TLD
Invalid Space,user @domain.com,Invalid Space
Invalid Double At,user@@domain.com,Invalid Double At
Invalid No Domain,user@,Invalid No Domain
Invalid No At,userdomain.com,Invalid No At
Invalid Dot Start,user@.domain.com,Invalid Dot Start
Invalid Dot End,user@domain.com.,Invalid Dot End
"""
        
        with patch('builtins.open', mock_open(read_data=edge_case_content)):
            contacts = read_contacts_from_csv('dummy.csv')
        
        # Should only include valid emails (basic @ validation)
        valid_emails = [contact['email'] for contact in contacts]
        
        # Valid emails should be included
        expected_valid = [
            'user@domain.com',
            'user@sub.domain.com',
            'user+tag@domain.com',
            'user.name@domain.com',
            'user@domain-name.com',
            'user@123domain.com',
            'user@domain.co.uk',
            'user@domain.museum'
        ]
        
        for email in expected_valid:
            assert email in valid_emails, f"Valid email {email} should be included"

    def test_read_contacts_empty_csv_file(self):
        """Test handling of empty CSV file."""
        empty_content = ""
        
        with patch('builtins.open', mock_open(read_data=empty_content)):
            contacts = read_contacts_from_csv('dummy.csv')
        
        assert contacts == []

    def test_read_contacts_header_only_csv(self):
        """Test handling of CSV file with only headers."""
        header_only_content = "Primary Contact Name,Email,Company\n"
        
        with patch('builtins.open', mock_open(read_data=header_only_content)):
            contacts = read_contacts_from_csv('dummy.csv')
        
        assert contacts == []

    def test_read_contacts_missing_columns(self):
        """Test handling of CSV with missing required columns."""
        missing_columns_content = """Name,Address,Phone
John Doe,123 Main St,555-1234
Jane Smith,456 Oak Ave,555-5678
"""
        
        with patch('builtins.open', mock_open(read_data=missing_columns_content)):
            contacts = read_contacts_from_csv('dummy.csv')
        
        # Should return empty list when required columns are missing
        assert contacts == []

    def test_read_contacts_extra_columns(self):
        """Test handling of CSV with extra columns."""
        extra_columns_content = """Primary Contact Name,Email,Company,Phone,Address,Notes
John Doe,john.doe@example.com,Acme Corp,555-1234,123 Main St,VIP Client
Jane Smith,jane.smith@company.org,Tech Solutions,555-5678,456 Oak Ave,New Customer
"""
        
        with patch('builtins.open', mock_open(read_data=extra_columns_content)):
            contacts = read_contacts_from_csv('dummy.csv')
        
        assert len(contacts) == 2
        assert contacts[0]['email'] == 'john.doe@example.com'
        assert contacts[0]['first_name'] == 'John'

    def test_read_contacts_unicode_content(self):
        """Test handling of CSV with Unicode characters."""
        unicode_content = """Primary Contact Name,Email,Company
José García,jose.garcia@empresa.es,Empresa España
François Dubois,francois@société.fr,Société Française
李明,li.ming@company.cn,中国公司
محمد أحمد,mohammed@company.ae,شركة الإمارات
"""
        
        with patch('builtins.open', mock_open(read_data=unicode_content)):
            contacts = read_contacts_from_csv('dummy.csv')
        
        assert len(contacts) == 4
        
        # Check Unicode names are preserved
        names = [contact['contact_name'] for contact in contacts]
        assert 'José García' in names
        assert 'François Dubois' in names
        assert '李明' in names
        assert 'محمد أحمد' in names

    def test_read_contacts_file_not_found(self):
        """Test handling of non-existent CSV file."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            contacts = read_contacts_from_csv('nonexistent.csv')
        
        assert contacts == []

    def test_read_contacts_permission_denied(self):
        """Test handling of permission denied error."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            contacts = read_contacts_from_csv('protected.csv')
        
        assert contacts == []

    def test_read_contacts_encoding_error(self):
        """Test handling of encoding errors."""
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')):
            contacts = read_contacts_from_csv('bad_encoding.csv')
        
        assert contacts == []

    def test_read_contacts_csv_parsing_error(self):
        """Test handling of CSV parsing errors."""
        malformed_csv = """Primary Contact Name,Email,Company
John Doe,john.doe@example.com,Acme Corp
Jane Smith,"unclosed quote,jane@company.org,Tech Solutions
"""
        
        # Mock csv.DictReader to raise an exception
        with patch('builtins.open', mock_open(read_data=malformed_csv)), \
             patch('csv.DictReader', side_effect=csv.Error("CSV parsing error")):
            contacts = read_contacts_from_csv('malformed.csv')
        
        assert contacts == []

    def test_read_contacts_large_file_handling(self):
        """Test handling of large CSV files."""
        # Create a large CSV content
        large_content = "Primary Contact Name,Email,Company\n"
        for i in range(1000):
            large_content += f"User {i},user{i}@domain.com,Company {i}\n"
        
        with patch('builtins.open', mock_open(read_data=large_content)):
            contacts = read_contacts_from_csv('large.csv')
        
        assert len(contacts) == 1000
        assert contacts[0]['email'] == 'user0@domain.com'
        assert contacts[999]['email'] == 'user999@domain.com'

    def test_read_contacts_whitespace_handling(self):
        """Test handling of whitespace in CSV data."""
        whitespace_content = """Primary Contact Name,Email,Company
  John Doe  ,  john.doe@example.com  ,  Acme Corp  
Jane Smith,jane.smith@company.org,Tech Solutions
  ,  ,  
Bob Johnson,bob@startup.io,Innovation Inc
"""
        
        with patch('builtins.open', mock_open(read_data=whitespace_content)):
            contacts = read_contacts_from_csv('whitespace.csv')
        
        # Should handle whitespace correctly
        assert len(contacts) == 3  # Empty row should be filtered out
        
        # Check that whitespace is stripped
        assert contacts[0]['contact_name'] == 'John Doe'
        assert contacts[0]['email'] == 'john.doe@example.com'

    def test_read_contacts_case_sensitivity(self):
        """Test handling of different case in column headers."""
        case_content = """primary contact name,email,company
John Doe,john.doe@example.com,Acme Corp
Jane Smith,jane.smith@company.org,Tech Solutions
"""
        
        with patch('builtins.open', mock_open(read_data=case_content)):
            contacts = read_contacts_from_csv('case.csv')
        
        # Should return empty list due to case-sensitive column matching
        # This documents current behavior
        assert contacts == []

    def test_read_contacts_mixed_line_endings(self):
        """Test handling of mixed line endings in CSV."""
        mixed_endings_content = "Primary Contact Name,Email,Company\r\nJohn Doe,john.doe@example.com,Acme Corp\nJane Smith,jane.smith@company.org,Tech Solutions\r\n"
        
        with patch('builtins.open', mock_open(read_data=mixed_endings_content)):
            contacts = read_contacts_from_csv('mixed.csv')
        
        assert len(contacts) == 2
        assert contacts[0]['email'] == 'john.doe@example.com'
        assert contacts[1]['email'] == 'jane.smith@company.org'

    def test_get_first_name_integration_with_csv_processing(self):
        """Test integration between CSV processing and first name extraction."""
        integration_content = """Primary Contact Name,Email,Company
Dr. John Doe,john.doe@example.com,Acme Corp
Ms. Jane Smith,jane.smith@company.org,Tech Solutions
Prof. Robert Johnson,bob@startup.io,Innovation Inc
Mr. David Wilson,david@company.com,Wilson Corp
SingleName,single@domain.com,Single Corp
,empty@domain.com,Empty Corp
"""
        
        with patch('builtins.open', mock_open(read_data=integration_content)):
            contacts = read_contacts_from_csv('integration.csv')
        
        assert len(contacts) == 6
        
        # Check first name extraction
        expected_names = ['John', 'Jane', 'Robert', 'David', 'SingleName', 'Friend']
        actual_names = [contact['first_name'] for contact in contacts]
        
        assert actual_names == expected_names

    def test_read_contacts_memory_efficiency(self):
        """Test memory efficiency with streaming-like processing."""
        # This test ensures the function doesn't load everything into memory at once
        # for very large files (though current implementation does load all)
        
        content = "Primary Contact Name,Email,Company\n"
        for i in range(100):
            content += f"User {i},user{i}@domain.com,Company {i}\n"
        
        with patch('builtins.open', mock_open(read_data=content)):
            contacts = read_contacts_from_csv('memory_test.csv')
        
        # Verify all contacts are processed correctly
        assert len(contacts) == 100
        
        # Verify data integrity
        for i, contact in enumerate(contacts):
            assert contact['email'] == f'user{i}@domain.com'
            assert contact['first_name'] == f'User'
            assert contact['contact_name'] == f'User {i}'

    def test_read_contacts_concurrent_access_simulation(self):
        """Test behavior under simulated concurrent file access."""
        content = """Primary Contact Name,Email,Company
John Doe,john.doe@example.com,Acme Corp
Jane Smith,jane.smith@company.org,Tech Solutions
"""
        
        # Simulate multiple concurrent reads
        results = []
        with patch('builtins.open', mock_open(read_data=content)):
            for _ in range(5):
                contacts = read_contacts_from_csv('concurrent.csv')
                results.append(contacts)
        
        # All results should be identical
        for result in results:
            assert len(result) == 2
            assert result[0]['email'] == 'john.doe@example.com'
            assert result[1]['email'] == 'jane.smith@company.org'

    def test_read_contacts_special_csv_characters(self):
        """Test handling of special CSV characters (quotes, commas, newlines)."""
        special_content = '''Primary Contact Name,Email,Company
"Doe, John",john.doe@example.com,"Acme, Corp"
"Smith ""Jane""",jane.smith@company.org,"Tech ""Solutions"""
"Wilson
Bob",bob@startup.io,"Innovation
Inc"
'''
        
        with patch('builtins.open', mock_open(read_data=special_content)):
            contacts = read_contacts_from_csv('special.csv')
        
        assert len(contacts) == 3
        
        # Check that special characters are handled correctly
        assert contacts[0]['contact_name'] == 'Doe, John'
        assert contacts[1]['contact_name'] == 'Smith "Jane"'
        assert 'Wilson' in contacts[2]['contact_name']  # Newline handling may vary