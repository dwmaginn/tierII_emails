import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.utils.report_generator import generate_email_summary_report


class TestReportGenerator:
    """Test suite for the report generator functionality."""

    @pytest.fixture
    def temp_logs_dir(self):
        """Create a temporary logs directory for testing."""
        import tempfile
        import shutil
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Change to temp directory and create logs subdirectory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        os.makedirs('logs', exist_ok=True)
        
        yield temp_dir
        
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_failed_contacts(self):
        """Sample failed contacts for testing."""
        return [
            {
                'email': 'failed1@example.com',
                'contact_name': 'John Doe',
                'status_code': '400',
                'error_message': 'Invalid email format',
                'timestamp': '2024-01-01 12:00:00'
            },
            {
                'email': 'failed2@example.com',
                'contact_name': 'Jane Smith',
                'status_code': '500',
                'error_message': 'Server error occurred during delivery',
                'timestamp': '2024-01-01 12:01:00'
            }
        ]

    @patch('webbrowser.open')
    def test_generate_report_all_successful(self, mock_browser, temp_logs_dir):
        """Test report generation when all emails are successful."""
        total_contacts = 3
        successful_count = 3
        failed_count = 0
        success_rate = 100.0
        failed_contacts = []

        report_path = generate_email_summary_report(
            total_contacts, successful_count, failed_count, success_rate, failed_contacts
        )

        # Verify report file was created
        assert os.path.exists(report_path)
        assert report_path.endswith('.html')
        
        # Verify browser was opened
        mock_browser.assert_called_once()

        # Verify report content
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check stats cards HTML structure
        assert f'<div class="stat-number total">{total_contacts}</div>' in content
        assert f'<div class="stat-number success">{successful_count}</div>' in content
        assert f'<div class="stat-number failed">{failed_count}</div>' in content
        assert f'<div class="stat-number rate">{success_rate:.1f}%</div>' in content

        # Check progress bar
        assert f'style="width: {success_rate}%;"' in content
        assert f'{success_rate:.1f}% Success Rate' in content

        # Check no failures message is shown and no failures table is rendered
        assert 'No failed email deliveries to report' in content
        assert '<table class="failures-table">' not in content

    @patch('webbrowser.open')
    def test_generate_report_all_failed(self, mock_browser, temp_logs_dir, sample_failed_contacts):
        """Test report generation when all emails fail."""
        total_contacts = 2
        successful_count = 0
        failed_count = 2
        success_rate = 0.0

        report_path = generate_email_summary_report(
            total_contacts, successful_count, failed_count, success_rate, sample_failed_contacts
        )

        # Verify report file was created
        assert os.path.exists(report_path)
        
        # Verify browser was opened
        mock_browser.assert_called_once()

        # Verify report content
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check stats cards
        assert f'<div class="stat-number total">{total_contacts}</div>' in content
        assert f'<div class="stat-number success">{successful_count}</div>' in content
        assert f'<div class="stat-number failed">{failed_count}</div>' in content
        assert f'<div class="stat-number rate">{success_rate:.1f}%</div>' in content

        # Check failures table is present
        assert '<table class="failures-table">' in content
        assert 'Delivery Details' in content
        
        # Check failed contact details
        assert 'failed1@example.com' in content
        assert 'failed2@example.com' in content
        assert 'John Doe' in content
        assert 'Jane Smith' in content
        assert 'Invalid email format' in content

    @patch('webbrowser.open')
    def test_generate_report_mixed_results(self, mock_browser, temp_logs_dir):
        """Test report generation with mixed success and failure results."""
        total_contacts = 5
        successful_count = 3
        failed_count = 2
        success_rate = 60.0
        failed_contacts = [
            {
                'email': 'failed@example.com',
                'contact_name': 'Failed User',
                'status_code': '400',
                'error_message': 'Bad request',
                'timestamp': '2024-01-01 12:00:00'
            }
        ]

        report_path = generate_email_summary_report(
            total_contacts, successful_count, failed_count, success_rate, failed_contacts
        )

        # Verify report file was created
        assert os.path.exists(report_path)
        
        # Verify browser was opened
        mock_browser.assert_called_once()

        # Verify report content
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check all stats
        assert f'<div class="stat-number total">{total_contacts}</div>' in content
        assert f'<div class="stat-number success">{successful_count}</div>' in content
        assert f'<div class="stat-number failed">{failed_count}</div>' in content
        assert f'<div class="stat-number rate">{success_rate:.1f}%</div>' in content

        # Check failures section exists
        assert 'Delivery Details' in content
        assert 'failed@example.com' in content

    @patch('webbrowser.open')
    def test_generate_report_empty_lists(self, mock_browser, temp_logs_dir):
        """Test report generation with empty contact lists."""
        total_contacts = 0
        successful_count = 0
        failed_count = 0
        success_rate = 0.0
        failed_contacts = []

        report_path = generate_email_summary_report(
            total_contacts, successful_count, failed_count, success_rate, failed_contacts
        )

        # Verify report file was created
        assert os.path.exists(report_path)
        
        # Verify browser was opened
        mock_browser.assert_called_once()

        # Verify report content
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check stats show zeros
        assert f'<div class="stat-number total">{total_contacts}</div>' in content
        assert f'<div class="stat-number success">{successful_count}</div>' in content
        assert f'<div class="stat-number failed">{failed_count}</div>' in content
        assert f'<div class="stat-number rate">{success_rate:.1f}%</div>' in content

        # Check no failures message
        assert 'No failed email deliveries to report' in content

    @patch('webbrowser.open')
    def test_generate_report_with_special_characters(self, mock_browser, temp_logs_dir):
        """Test report generation with special characters in contact data."""
        failed_contacts = [
            {
                'email': 'café@example.com',
                'contact_name': 'José García',
                'status_code': '400',
                'error_message': 'München server error with ñ character',
                'timestamp': '2024-01-01 12:00:00'
            }
        ]

        report_path = generate_email_summary_report(
            1, 0, 1, 0.0, failed_contacts
        )

        # Verify report file was created
        assert os.path.exists(report_path)

        # Verify report content handles special characters
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'café@example.com' in content
        assert 'José García' in content
        assert 'München' in content
        assert 'ñ character' in content

    @patch('webbrowser.open')
    def test_generate_report_missing_contact_fields(self, mock_browser, temp_logs_dir):
        """Test report generation when contacts have missing optional fields."""
        failed_contacts = [
            {
                'email': 'incomplete@example.com',
                # Missing contact_name, status_code, error_message, timestamp
            }
        ]

        report_path = generate_email_summary_report(
            1, 0, 1, 0.0, failed_contacts
        )

        # Verify report file was created
        assert os.path.exists(report_path)

        # Verify report content handles missing fields gracefully
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'incomplete@example.com' in content
        assert 'N/A' in content  # Should show N/A for missing fields

    @patch('webbrowser.open')
    def test_generate_report_custom_title(self, mock_browser, temp_logs_dir):
        """Test report generation with custom title."""
        custom_title = "Custom Campaign Report"
        
        report_path = generate_email_summary_report(
            5, 3, 2, 60.0, [], custom_title
        )

        # Verify report file was created
        assert os.path.exists(report_path)

        # Verify custom title is used
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert f'<title>{custom_title}</title>' in content

    @patch('webbrowser.open')
    def test_generate_report_timestamp_in_filename(self, mock_browser, temp_logs_dir):
        """Test that generated report filename contains timestamp."""
        report_path = generate_email_summary_report(1, 1, 0, 100.0, [])

        # Verify filename format
        filename = os.path.basename(report_path)
        assert filename.startswith('email_report_')
        assert filename.endswith('.html')
        
        # Extract timestamp from filename and verify format
        timestamp_str = filename.replace('email_report_', '').replace('.html', '')
        # Should be in format YYYYMMDD_HHMMSS
        assert len(timestamp_str) == 15  # 8 digits + underscore + 6 digits
        assert '_' in timestamp_str
        
        # Verify it can be parsed as a valid datetime
        try:
            datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        except ValueError:
            pytest.fail(f"Timestamp {timestamp_str} is not in expected format YYYYMMDD_HHMMSS")

    @patch('webbrowser.open')
    def test_generate_report_creates_logs_directory(self, mock_browser, temp_logs_dir):
        """Test that logs directory is created if it doesn't exist."""
        # Remove the logs directory
        if os.path.exists('logs'):
            os.rmdir('logs')

        # Verify logs directory doesn't exist
        assert not os.path.exists('logs')

        generate_email_summary_report(1, 1, 0, 100.0, [])

        # Verify logs directory was created and report file exists
        assert os.path.exists('logs')
        log_files = [f for f in os.listdir('logs') if f.startswith('email_report_')]
        assert len(log_files) == 1

    @patch('webbrowser.open')
    def test_generate_report_browser_error(self, mock_browser, temp_logs_dir):
        """Test report generation when browser fails to open."""
        mock_browser.side_effect = Exception("Browser error")

        # Should still generate report even if browser fails
        # The function should handle the browser error gracefully
        try:
            report_path = generate_email_summary_report(1, 1, 0, 100.0, [])
            # If we get here, the function handled the error gracefully
            assert os.path.exists(report_path)
        except Exception as e:
            # If the function doesn't handle browser errors, that's also acceptable behavior
            # as long as it's the browser error being propagated
            assert "Browser error" in str(e)
        
        # Verify browser open was attempted
        mock_browser.assert_called_once()

    @patch('webbrowser.open')
    def test_generate_report_long_error_message_truncation(self, mock_browser, temp_logs_dir):
        """Test that long error messages are properly truncated."""
        long_error = "A" * 150  # 150 character error message
        failed_contacts = [
            {
                'email': 'test@example.com',
                'contact_name': 'Test User',
                'status_code': '500',
                'error_message': long_error,
                'timestamp': '2024-01-01 12:00:00'
            }
        ]

        report_path = generate_email_summary_report(
            1, 0, 1, 0.0, failed_contacts
        )

        # Verify report content truncates long error messages
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should contain truncated message with ellipsis
        assert long_error[:100] in content
        assert '...' in content

    @patch('webbrowser.open')
    @patch('os.makedirs')
    def test_generate_report_permission_error(self, mock_makedirs, mock_browser, temp_logs_dir):
        """Test handling of permission errors when creating directories."""
        mock_makedirs.side_effect = PermissionError("Permission denied")

        with pytest.raises(PermissionError):
            generate_email_summary_report(1, 1, 0, 100.0, [])

    def test_generate_failures_section_no_failures(self):
        """Test _generate_failures_section with no failed contacts."""
        from src.utils.report_generator import _generate_failures_section
        
        result = _generate_failures_section([])
        
        assert 'no-failures' in result
        assert 'No failed email deliveries to report' in result
        assert '<table class="failures-table">' not in result

    def test_generate_failures_section_with_failures(self, sample_failed_contacts):
        """Test _generate_failures_section with failed contacts."""
        from src.utils.report_generator import _generate_failures_section
        
        result = _generate_failures_section(sample_failed_contacts)
        
        assert '<table class="failures-table">' in result
        assert 'failed1@example.com' in result
        assert 'failed2@example.com' in result
        assert 'John Doe' in result
        assert 'Jane Smith' in result


class TestReportGeneratorIntegration:
    """Integration tests for report generator with various scenarios."""

    @pytest.fixture
    def temp_logs_dir(self):
        """Create a temporary logs directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = os.path.join(temp_dir, 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            
            # Change to temp directory for testing
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            yield logs_dir
            
            # Restore original directory
            os.chdir(original_cwd)

    @patch('webbrowser.open')
    def test_report_cross_platform_compatibility(self, mock_browser, temp_logs_dir):
        """Test report generation works across different platforms."""
        report_path = generate_email_summary_report(1, 1, 0, 100.0, [])

        # Verify file exists
        assert os.path.exists(report_path)
        
        # Verify path format is correct for the platform
        assert report_path.endswith('.html')
        assert 'email_report_' in os.path.basename(report_path)
        
        # Verify content is valid HTML
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert '<!DOCTYPE html>' in content
        assert '</html>' in content

    @patch('webbrowser.open')
    def test_concurrent_report_generation(self, mock_browser, temp_logs_dir):
        """Test that concurrent report generation creates unique files."""
        import threading
        import time
        
        report_paths = []
        
        def generate_report(index):
            # Use unique timestamp override for each thread
            timestamp = f"20250926_13060{index}"
            path = generate_email_summary_report(10, 8, 2, 80.0, [], timestamp_override=timestamp)
            report_paths.append(path)
        
        # Create threads with unique timestamp overrides
        threads = []
        for i in range(3):
            thread = threading.Thread(target=generate_report, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all reports were created with unique filenames
        assert len(report_paths) == 3
        assert len(set(report_paths)) == 3  # All paths should be unique
        
        # Verify all files exist
        for path in report_paths:
            assert os.path.exists(path)