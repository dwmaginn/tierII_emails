"""Unit tests for utils package initialization."""

import pytest
from src.utils import load_contacts, validate_contact_data
import src.utils


class TestUtilsPackageInit:
    """Test cases for utils package initialization."""
    
    def test_imports_available(self):
        """Test that imported functions are available in the package."""
        # Test that functions are importable
        assert callable(load_contacts)
        assert callable(validate_contact_data)
    
    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        expected_exports = ['load_contacts', 'validate_contact_data']
        assert src.utils.__all__ == expected_exports
    
    def test_functions_work_correctly(self):
        """Test that imported functions work as expected."""
        # Test validate_contact_data with valid data
        valid_contacts = [{'email': 'test@example.com'}]
        assert validate_contact_data(valid_contacts) is True
        
        # Test validate_contact_data with invalid data
        invalid_contacts = [{'name': 'No Email'}]
        assert validate_contact_data(invalid_contacts) is False