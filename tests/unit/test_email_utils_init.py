"""Unit tests for email_utils package initialization."""

import src.email_utils


class TestEmailUtilsPackageInit:
    """Test cases for email_utils package initialization."""
    
    def test_all_exports_empty(self):
        """Test that __all__ is empty as expected."""
        assert src.email_utils.__all__ == []
    
    def test_package_docstring(self):
        """Test that package has proper docstring."""
        assert src.email_utils.__doc__ == "Email utilities package."