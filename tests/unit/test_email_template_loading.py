"""Comprehensive tests for email template loading and personalization.

This module tests the load_email_template() function from email_campaign.py,
covering file I/O operations, template personalization, fallback mechanisms,
and error handling scenarios.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, Mock, mock_open
from pathlib import Path

# Import the function under test
from src.email_campaign import load_email_template


class TestEmailTemplateLoading:
    """Test suite for email template loading functionality."""

    @pytest.fixture
    def temp_template_file(self):
        """Create a temporary template file for testing."""
        content = """
        <html>
        <body>
            <h1>Hello {first_name}!</h1>
            <p>Welcome to our service, {first_name}.</p>
            <p>Best regards,<br>The Team</p>
        </body>
        </html>
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except FileNotFoundError:
            pass

    @pytest.fixture
    def mock_settings_with_template_path(self, temp_template_file):
        """Mock settings with custom template path."""
        with patch('src.email_campaign.settings') as mock_settings:
            mock_settings.email_template_path = temp_template_file
            yield mock_settings

    @pytest.fixture
    def mock_settings_no_template_path(self):
        """Mock settings without custom template path."""
        with patch('src.email_campaign.settings') as mock_settings:
            mock_settings.email_template_path = None
            yield mock_settings

    def test_load_template_with_custom_path_success(self, mock_settings_with_template_path):
        """Test successful template loading with custom template path."""
        result = load_email_template("John")
        
        assert "Hello John!" in result
        assert "Welcome to our service, John." in result
        assert "<html>" in result
        assert "<body>" in result

    def test_load_template_personalization(self, mock_settings_with_template_path):
        """Test template personalization with different names."""
        test_cases = [
            ("Alice", "Hello Alice!"),
            ("Bob", "Welcome to our service, Bob."),
            ("María", "Hello María!"),
            ("Jean-Pierre", "Welcome to our service, Jean-Pierre."),
            ("", "Hello !"),  # Edge case: empty name
        ]
        
        for first_name, expected_text in test_cases:
            result = load_email_template(first_name)
            assert expected_text in result

    def test_load_template_with_default_path_success(self, mock_settings_no_template_path):
        """Test template loading with default path when custom path not set."""
        # Create a mock template file at the default location
        template_content = "<html><body>Hi {first_name}!</body></html>"
        
        with patch('os.path.exists') as mock_exists, \
             patch('builtins.open', mock_open(read_data=template_content)):
            mock_exists.return_value = True
            
            result = load_email_template("Sarah")
            
            assert "Hi Sarah!" in result
            assert "<html>" in result

    def test_load_template_file_not_found_fallback(self, mock_settings_no_template_path):
        """Test fallback to plain text when template file not found."""
        with patch('os.path.exists', return_value=False):
            result = load_email_template("David")
            
            # Should fallback to plain text template
            assert "Hi David," in result
            assert "Honest Pharmco" in result
            assert "contact@honestpharmco.com" in result
            assert "<html>" not in result  # Should be plain text

    def test_load_template_file_read_error_fallback(self, mock_settings_with_template_path):
        """Test fallback when file exists but cannot be read."""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = load_email_template("Emma")
            
            # Should fallback to plain text template
            assert "Hi Emma," in result
            assert "Honest Pharmco" in result
            assert "<html>" not in result

    def test_load_template_encoding_error_fallback(self, mock_settings_no_template_path):
        """Test fallback when file has encoding issues."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')):
            result = load_email_template("Carlos")
            
            # Should fallback to plain text template
            assert "Hi Carlos," in result
            assert "Honest Pharmco" in result

    def test_load_template_empty_file_fallback(self, mock_settings_no_template_path):
        """Test fallback when template file is empty."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="")):
            result = load_email_template("Lisa")
            
            # Should still personalize empty content
            assert result == ""

    def test_load_template_malformed_html_handling(self, mock_settings_no_template_path):
        """Test handling of malformed HTML in template."""
        malformed_html = "<html><body><h1>Hello {first_name}!</h1><p>Unclosed paragraph</body></html>"
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=malformed_html)):
            result = load_email_template("Mike")
            
            # Should still personalize despite malformed HTML
            assert "Hello Mike!" in result
            assert "<html>" in result

    def test_load_template_multiple_placeholders(self, mock_settings_no_template_path):
        """Test template with multiple {first_name} placeholders."""
        template_content = """
        <html>
        <body>
            <h1>Dear {first_name},</h1>
            <p>Hello {first_name}, how are you?</p>
            <p>We hope you're doing well, {first_name}!</p>
            <p>Sincerely, {first_name}'s support team</p>
        </body>
        </html>
        """
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=template_content)):
            result = load_email_template("Anna")
            
            # All placeholders should be replaced
            assert result.count("Anna") == 4
            assert "{first_name}" not in result

    def test_load_template_special_characters_in_name(self, mock_settings_no_template_path):
        """Test template personalization with special characters in names."""
        template_content = "<html><body>Hello {first_name}!</body></html>"
        
        special_names = [
            "José",
            "François",
            "Müller",
            "O'Connor",
            "李明",
            "محمد",
            "Владимир"
        ]
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=template_content)):
            for name in special_names:
                result = load_email_template(name)
                assert f"Hello {name}!" in result

    def test_load_template_settings_attribute_error(self):
        """Test handling when settings object has attribute errors."""
        with patch('src.email_campaign.settings') as mock_settings:
            # Simulate AttributeError when accessing email_template_path
            type(mock_settings).email_template_path = Mock(side_effect=AttributeError())
            
            with patch('os.path.exists', return_value=False):
                result = load_email_template("Test")
                
                # Should fallback to plain text
                assert "Hi Test," in result

    def test_load_template_settings_mock_object_handling(self):
        """Test handling when settings.email_template_path is a Mock object."""
        with patch('src.email_campaign.settings') as mock_settings:
            # Set email_template_path to a Mock object (not a string)
            mock_settings.email_template_path = Mock()
            
            with patch('os.path.exists', return_value=False):
                result = load_email_template("Test")
                
                # Should fallback to plain text since Mock is not a string
                assert "Hi Test," in result

    def test_load_template_path_traversal_security(self, mock_settings_no_template_path):
        """Test that path traversal attempts are handled safely."""
        # This test ensures the function doesn't blindly trust file paths
        malicious_path = "../../../../etc/passwd"
        
        with patch('src.email_campaign.settings') as mock_settings:
            mock_settings.email_template_path = malicious_path
            
            with patch('os.path.exists', return_value=False):
                result = load_email_template("Hacker")
                
                # Should fallback to plain text when file doesn't exist
                assert "Hi Hacker," in result

    def test_load_template_large_file_handling(self, mock_settings_no_template_path):
        """Test handling of large template files."""
        # Simulate a large template file
        large_content = "<html><body>Hello {first_name}!</body></html>" * 1000
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=large_content)):
            result = load_email_template("BigFile")
            
            # Should handle large files correctly
            assert "Hello BigFile!" in result
            assert result.count("BigFile") == 1000

    def test_load_template_concurrent_access_simulation(self, mock_settings_no_template_path):
        """Test template loading under simulated concurrent access."""
        template_content = "<html><body>Hello {first_name}!</body></html>"
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=template_content)):
            
            # Simulate multiple concurrent calls
            names = ["User1", "User2", "User3", "User4", "User5"]
            results = []
            
            for name in names:
                result = load_email_template(name)
                results.append(result)
            
            # All results should be properly personalized
            for i, result in enumerate(results):
                assert f"Hello {names[i]}!" in result

    def test_load_template_fallback_content_structure(self):
        """Test the structure and content of fallback template."""
        with patch('os.path.exists', return_value=False):
            result = load_email_template("TestUser")
            
            # Verify fallback template structure
            assert "Hi TestUser," in result
            assert "Honest Pharmco" in result
            assert "contact@honestpharmco.com" in result
            assert "(555) 123-4567" in result
            assert "David Maginn" in result
            
            # Should be plain text, not HTML
            assert "<html>" not in result
            assert "<body>" not in result
            assert "<p>" not in result

    def test_load_template_none_input_handling(self):
        """Test handling of None as first_name input."""
        with patch('os.path.exists', return_value=False):
            # This should not crash, but handle None gracefully
            result = load_email_template(None)
            
            # Should replace {first_name} with None (converted to string)
            assert "Hi None," in result

    def test_load_template_numeric_input_handling(self):
        """Test handling of numeric input as first_name."""
        with patch('os.path.exists', return_value=False):
            result = load_email_template(123)
            
            # Should convert number to string and use it
            assert "Hi 123," in result

    def test_load_template_boolean_input_handling(self):
        """Test handling of boolean input as first_name."""
        with patch('os.path.exists', return_value=False):
            result = load_email_template(True)
            
            # Should convert boolean to string
            assert "Hi True," in result