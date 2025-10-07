"""Comprehensive test suite for main.py email campaign functionality."""

import pytest
import os
import json
import tempfile
import logging
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
from io import StringIO

from src.main import (
    ColoredFormatter, 
    setup_logging, 
    log_failed_emails, 
    log_successful_emails, 
    send_in_bulk
)


class TestColoredFormatter:
    """Test suite for ColoredFormatter class."""
    
    def test_colored_formatter_initialization(self):
        """Test ColoredFormatter can be initialized."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        assert formatter is not None
        assert hasattr(formatter, 'COLORS')
    
    def test_colored_formatter_colors_defined(self):
        """Test that all log levels have colors defined."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        expected_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        for level in expected_levels:
            assert level in formatter.COLORS
            assert formatter.COLORS[level] is not None
    
    def test_colored_formatter_format_with_color(self):
        """Test formatting with color for known log levels."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        
        # Create a mock log record
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='Test message', args=(), exc_info=None
        )
        
        formatted = formatter.format(record)
        assert 'Test message' in formatted
        assert 'INFO' in formatted
    
    def test_colored_formatter_format_unknown_level(self):
        """Test formatting with unknown log level (no color)."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        
        # Create a mock log record with custom level
        record = logging.LogRecord(
            name='test', level=99, pathname='', lineno=0,
            msg='Test message', args=(), exc_info=None
        )
        record.levelname = 'CUSTOM'
        
        formatted = formatter.format(record)
        assert 'Test message' in formatted
        assert 'CUSTOM' in formatted


class TestSetupLogging:
    """Test suite for setup_logging function."""
    
    @patch('os.makedirs')
    @patch('logging.getLogger')
    def test_setup_logging_creates_logs_directory(self, mock_get_logger, mock_makedirs):
        """Test that setup_logging creates logs directory."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        setup_logging()
        
        mock_makedirs.assert_called_once_with('logs', exist_ok=True)
    
    @patch('os.makedirs')
    @patch('logging.getLogger')
    def test_setup_logging_configures_logger(self, mock_get_logger, mock_makedirs):
        """Test that setup_logging properly configures logger."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        result = setup_logging()
        
        # Verify logger configuration
        mock_logger.setLevel.assert_called_once_with(logging.INFO)
        mock_logger.handlers.clear.assert_called_once()
        assert mock_logger.addHandler.call_count == 2  # File and console handlers
        mock_logger.info.assert_called_once()
        assert result == mock_logger
    
    @patch('os.makedirs')
    @patch('logging.FileHandler')
    @patch('logging.StreamHandler')
    @patch('logging.getLogger')
    def test_setup_logging_handlers_configuration(self, mock_get_logger, mock_stream_handler, mock_file_handler, mock_makedirs):
        """Test that handlers are properly configured."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_file_h = Mock()
        mock_stream_h = Mock()
        mock_file_handler.return_value = mock_file_h
        mock_stream_handler.return_value = mock_stream_h
        
        setup_logging()
        
        # Verify handlers are created and configured
        mock_file_handler.assert_called_once()
        mock_stream_handler.assert_called_once()
        mock_file_h.setFormatter.assert_called_once()
        mock_stream_h.setFormatter.assert_called_once()


class TestLogFailedEmails:
    """Test suite for log_failed_emails function."""
    
    def test_log_failed_emails_empty_list(self):
        """Test logging with empty failed contacts list."""
        # Should return early without creating file
        with patch('builtins.open', mock_open()) as mock_file:
            log_failed_emails([])
            mock_file.assert_not_called()
    
    @patch('csv.DictWriter')
    @patch('builtins.open', new_callable=mock_open)
    def test_log_failed_emails_creates_csv(self, mock_file, mock_dict_writer):
        """Test that failed emails are logged to CSV file."""
        failed_contacts = [
            {
                'Email': 'test@example.com',
                'Primary Contact Name': 'Test User',
                'email_status': 'failed',
                'error_message': 'Test error',
                'timestamp': '2024-01-01 12:00:00'
            }
        ]
        
        mock_writer = Mock()
        mock_dict_writer.return_value = mock_writer
        
        log_failed_emails(failed_contacts)
        
        # Verify file operations
        mock_file.assert_called_once_with('logs/failures.csv', 'w', newline='', encoding='utf-8')
        mock_dict_writer.assert_called_once()
        mock_writer.writeheader.assert_called_once()
        mock_writer.writerows.assert_called_once_with(failed_contacts)
    
    @patch('csv.DictWriter')
    @patch('builtins.open', new_callable=mock_open)
    def test_log_failed_emails_fieldnames(self, mock_file, mock_dict_writer):
        """Test that correct fieldnames are used for CSV."""
        failed_contacts = [{'Email': 'test@example.com'}]
        
        log_failed_emails(failed_contacts)
        
        # Verify fieldnames include all required fields
        call_args = mock_dict_writer.call_args
        fieldnames = call_args[1]['fieldnames']
        
        expected_fields = [
            'License Number', 'Email', 'first_name', 'email_status', 
            'status_code', 'error_message', 'timestamp'
        ]
        for field in expected_fields:
            assert field in fieldnames


class TestLogSuccessfulEmails:
    """Test suite for log_successful_emails function."""
    
    def test_log_successful_emails_empty_successful(self):
        """Test logging when no successful emails exist."""
        contacts = [{'Email': 'test@example.com'}]
        failed_contacts = [{'Email': 'test@example.com'}]
        
        with patch('builtins.open', mock_open()) as mock_file:
            log_successful_emails(contacts, failed_contacts)
            mock_file.assert_not_called()
    
    @patch('csv.DictWriter')
    @patch('builtins.open', new_callable=mock_open)
    def test_log_successful_emails_creates_csv(self, mock_file, mock_dict_writer):
        """Test that successful emails are logged to CSV file."""
        contacts = [
            {'Email': 'success@example.com', 'Primary Contact Name': 'Success User'},
            {'Email': 'failed@example.com', 'Primary Contact Name': 'Failed User'}
        ]
        failed_contacts = [{'Email': 'failed@example.com'}]
        
        mock_writer = Mock()
        mock_dict_writer.return_value = mock_writer
        
        log_successful_emails(contacts, failed_contacts)
        
        # Verify file operations
        mock_file.assert_called_once_with('logs/successful.csv', 'w', newline='', encoding='utf-8')
        mock_dict_writer.assert_called_once()
        mock_writer.writeheader.assert_called_once()
        mock_writer.writerow.assert_called_once()
    
    @patch('csv.DictWriter')
    @patch('builtins.open', new_callable=mock_open)
    def test_log_successful_emails_adds_tracking_fields(self, mock_file, mock_dict_writer):
        """Test that tracking fields are added to successful contacts."""
        contacts = [{'Email': 'success@example.com', 'Primary Contact Name': 'Success User'}]
        failed_contacts = []
        
        mock_writer = Mock()
        mock_dict_writer.return_value = mock_writer
        
        with patch('src.main.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '2024-01-01 12:00:00'
            log_successful_emails(contacts, failed_contacts)
        
        # Verify tracking fields are added
        call_args = mock_writer.writerow.call_args[0][0]
        assert call_args['email_status'] == 'success'
        assert call_args['timestamp'] == '2024-01-01 12:00:00'


class TestSendInBulk:
    """Test suite for send_in_bulk function."""
    
    @patch('src.main.generate_email_summary_report')
    @patch('src.main.log_successful_emails')
    @patch('src.main.log_failed_emails')
    @patch('src.main.time.sleep')
    @patch('src.main.tqdm')
    @patch('src.main.logger')
    @patch('src.main.EmailBuilder')
    @patch('src.main.MailerSendClient')
    @patch('src.main.parse_contacts_from_csv')
    @patch('src.main.load_email_config')
    @patch('src.main.request_blast_approval', return_value=True)
    @patch('os.getenv')
    def test_send_in_bulk_successful_campaign(self, mock_getenv, mock_approval, mock_load_config, mock_parse_contacts, 
                                            mock_mailersend, mock_email_builder, mock_logger, mock_tqdm,
                                            mock_sleep, mock_log_failed, mock_log_successful, mock_generate_report):
        """Test successful email campaign execution."""
        # Setup mocks
        mock_getenv.side_effect = lambda key: {
            'TIERII_MAILERSEND_API_TOKEN': 'test_token',
            'TIERII_SENDER_EMAIL': 'sender@test.com'
        }.get(key)
        
        mock_load_config.return_value = {
            'subject': 'Test Subject',
            'body': 'Hello {name}',
            'html_content': '<p>Hello {name}</p>'
        }
        
        mock_contacts = [
            {
                'Email': 'test1@example.com',
                'Primary Contact Name': 'Test User 1',
                'first_name': 'Test'
            }
        ]
        mock_parse_contacts.return_value = mock_contacts
        
        # Mock MailerSend client and response
        mock_client = Mock()
        mock_mailersend.return_value = mock_client
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client.emails.send.return_value = mock_response
        
        # Mock EmailBuilder
        mock_builder = Mock()
        mock_email_builder.return_value = mock_builder
        mock_builder.from_email.return_value = mock_builder
        mock_builder.to_many.return_value = mock_builder
        mock_builder.subject.return_value = mock_builder
        mock_builder.html.return_value = mock_builder
        mock_builder.text.return_value = mock_builder
        mock_builder.build.return_value = Mock()
        
        # Mock tqdm
        mock_tqdm.return_value = mock_contacts
        mock_tqdm.write = Mock()
        
        send_in_bulk()
        
        # Verify core functionality
        mock_parse_contacts.assert_called_once_with('data/test/testdata.csv')
        mock_mailersend.assert_called_once_with('test_token')
        mock_client.emails.send.assert_called_once()
        mock_log_failed.assert_called_once_with([])
        mock_log_successful.assert_called_once()
        mock_generate_report.assert_called_once()
    
    @patch('src.main.generate_email_summary_report')
    @patch('src.main.log_successful_emails')
    @patch('src.main.log_failed_emails')
    @patch('src.main.time.sleep')
    @patch('src.main.tqdm')
    @patch('src.main.logger')
    @patch('src.main.EmailBuilder')
    @patch('src.main.MailerSendClient')
    @patch('src.main.parse_contacts_from_csv')
    @patch('src.main.load_email_config')
    @patch('src.main.request_blast_approval', return_value=True)
    @patch('os.getenv')
    def test_send_in_bulk_failed_emails(self, mock_getenv, mock_approval, mock_load_config, mock_parse_contacts, 
                                       mock_mailersend, mock_email_builder, mock_logger, mock_tqdm,
                                       mock_sleep, mock_log_failed, mock_log_successful, mock_generate_report):
        """Test email campaign with failed emails."""
        # Setup mocks for failure scenario
        mock_getenv.side_effect = lambda key: {
            'TIERII_MAILERSEND_API_TOKEN': 'test_token',
            'TIERII_SENDER_EMAIL': 'sender@test.com'
        }.get(key)
        
        mock_load_config.return_value = {
            'subject': 'Test Subject',
            'body': 'Hello {name}',
            'html_content': '<p>Hello {name}</p>'
        }
        
        mock_contacts = [
            {
                'Email': 'test1@example.com',
                'Primary Contact Name': 'Test User 1',
                'first_name': 'Test'
            }
        ]
        mock_parse_contacts.return_value = mock_contacts
        
        # Mock MailerSend client with failure response
        mock_client = Mock()
        mock_mailersend.return_value = mock_client
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_client.emails.send.return_value = mock_response
        
        # Mock EmailBuilder
        mock_builder = Mock()
        mock_email_builder.return_value = mock_builder
        mock_builder.from_email.return_value = mock_builder
        mock_builder.to_many.return_value = mock_builder
        mock_builder.subject.return_value = mock_builder
        mock_builder.html.return_value = mock_builder
        mock_builder.text.return_value = mock_builder
        mock_builder.build.return_value = Mock()
        
        # Mock tqdm
        mock_tqdm.return_value = mock_contacts
        mock_tqdm.write = Mock()
        
        with patch('src.main.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '2024-01-01 12:00:00'
            send_in_bulk()
        
        # Verify failure handling
        mock_client.emails.send.assert_called_once()
        
        # Verify failed email logging
        failed_calls = mock_log_failed.call_args[0][0]
        assert len(failed_calls) == 1
        assert failed_calls[0]['email_status'] == 'failed'
        assert failed_calls[0]['status_code'] == 400
        assert failed_calls[0]['error_message'] == 'Bad Request'
    
    @patch('src.main.generate_email_summary_report')
    @patch('src.main.log_successful_emails')
    @patch('src.main.log_failed_emails')
    @patch('src.main.time.sleep')
    @patch('src.main.tqdm')
    @patch('src.main.logger')
    @patch('src.main.EmailBuilder')
    @patch('src.main.MailerSendClient')
    @patch('src.main.parse_contacts_from_csv')
    @patch('src.main.load_email_config')
    @patch('src.main.request_blast_approval', return_value=True)
    @patch('os.getenv')
    def test_send_in_bulk_exception_handling(self, mock_getenv, mock_approval, mock_load_config, mock_parse_contacts, 
                                           mock_mailersend, mock_email_builder, mock_logger, mock_tqdm,
                                           mock_sleep, mock_log_failed, mock_log_successful, mock_generate_report):
        """Test email campaign with exceptions during sending."""
        # Setup mocks
        mock_getenv.side_effect = lambda key: {
            'TIERII_MAILERSEND_API_TOKEN': 'test_token',
            'TIERII_SENDER_EMAIL': 'sender@test.com'
        }.get(key)
        
        mock_load_config.return_value = {
            'subject': 'Test Subject',
            'body': 'Hello {name}',
            'html_content': '<p>Hello {name}</p>'
        }
        
        mock_contacts = [
            {
                'Email': 'test1@example.com',
                'Primary Contact Name': 'Test User 1',
                'first_name': 'Test'
            }
        ]
        mock_parse_contacts.return_value = mock_contacts
        
        # Mock MailerSend client to raise exception
        mock_client = Mock()
        mock_mailersend.return_value = mock_client
        mock_client.emails.send.side_effect = Exception('Network error')
        
        # Mock EmailBuilder
        mock_builder = Mock()
        mock_email_builder.return_value = mock_builder
        mock_builder.from_email.return_value = mock_builder
        mock_builder.to_many.return_value = mock_builder
        mock_builder.subject.return_value = mock_builder
        mock_builder.html.return_value = mock_builder
        mock_builder.text.return_value = mock_builder
        mock_builder.build.return_value = Mock()
        
        # Mock tqdm
        mock_tqdm.return_value = mock_contacts
        mock_tqdm.write = Mock()
        
        with patch('src.main.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '2024-01-01 12:00:00'
            send_in_bulk()
        
        # Verify exception handling
        failed_calls = mock_log_failed.call_args[0][0]
        assert len(failed_calls) == 1
        assert failed_calls[0]['email_status'] == 'failed'
        assert failed_calls[0]['status_code'] == 'exception'
        assert failed_calls[0]['error_message'] == 'Network error'
    
    @patch('src.main.generate_email_summary_report')
    @patch('src.main.log_successful_emails')
    @patch('src.main.log_failed_emails')
    @patch('src.main.time.sleep')
    @patch('src.main.tqdm')
    @patch('src.main.logger')
    @patch('src.main.EmailBuilder')
    @patch('src.main.MailerSendClient')
    @patch('src.main.parse_contacts_from_csv')
    @patch('src.main.load_email_config')
    @patch('src.main.request_blast_approval', return_value=True)
    @patch('os.getenv')
    def test_send_in_bulk_empty_contacts(self, mock_getenv, mock_approval, mock_load_config, mock_parse_contacts, 
                                        mock_mailersend, mock_email_builder, mock_logger, mock_tqdm,
                                        mock_sleep, mock_log_failed, mock_log_successful, mock_generate_report):
        """Test email campaign with empty contacts list."""
        # Setup mocks
        mock_getenv.side_effect = lambda key: {
            'TIERII_MAILERSEND_API_TOKEN': 'test_token',
            'TIERII_SENDER_EMAIL': 'sender@test.com'
        }.get(key)
        
        mock_load_config.return_value = {
            'subject': 'Test Subject',
            'body': 'Hello {name}',
            'html_content': '<p>Hello {name}</p>'
        }
        
        mock_parse_contacts.return_value = []
        
        # Mock tqdm
        mock_tqdm.return_value = []
        mock_tqdm.write = Mock()
        
        send_in_bulk()
        
        # Verify behavior with empty contacts
        mock_log_failed.assert_called_once_with([])
        mock_log_successful.assert_called_once_with([], [])
        
        # Verify success rate calculation with empty list
        report_call = mock_generate_report.call_args
        assert report_call[1]['success_rate'] == 0
        assert report_call[1]['total_contacts'] == 0
    
    @patch('src.main.generate_email_summary_report')
    @patch('src.main.log_successful_emails')
    @patch('src.main.log_failed_emails')
    @patch('src.main.time.sleep')
    @patch('src.main.tqdm')
    @patch('src.main.logger')
    @patch('src.main.EmailBuilder')
    @patch('src.main.MailerSendClient')
    @patch('src.main.parse_contacts_from_csv')
    @patch('src.main.load_email_config')
    @patch('src.main.request_blast_approval', return_value=True)
    @patch('os.getenv')
    def test_send_in_bulk_success_rate_calculation(self, mock_getenv, mock_approval, mock_load_config, mock_parse_contacts, 
                                                  mock_mailersend, mock_email_builder, mock_logger, mock_tqdm,
                                                  mock_sleep, mock_log_failed, mock_log_successful, mock_generate_report):
        """Test success rate calculation with mixed results."""
        # Setup mocks
        mock_getenv.side_effect = lambda key: {
            'TIERII_MAILERSEND_API_TOKEN': 'test_token',
            'TIERII_SENDER_EMAIL': 'sender@test.com'
        }.get(key)
        
        mock_load_config.return_value = {
            'subject': 'Test Subject',
            'body': 'Hello {name}',
            'html_content': '<p>Hello {name}</p>'
        }
        
        mock_contacts = [
            {'Email': 'success@example.com', 'Primary Contact Name': 'Success User', 'first_name': 'Success'},
            {'Email': 'failed@example.com', 'Primary Contact Name': 'Failed User', 'first_name': 'Failed'}
        ]
        mock_parse_contacts.return_value = mock_contacts
        
        # Mock MailerSend client with mixed responses
        mock_client = Mock()
        mock_mailersend.return_value = mock_client
        
        responses = [Mock(status_code=202), Mock(status_code=400, text='Bad Request')]
        mock_client.emails.send.side_effect = responses
        
        # Mock EmailBuilder
        mock_builder = Mock()
        mock_email_builder.return_value = mock_builder
        mock_builder.from_email.return_value = mock_builder
        mock_builder.to_many.return_value = mock_builder
        mock_builder.subject.return_value = mock_builder
        mock_builder.html.return_value = mock_builder
        mock_builder.text.return_value = mock_builder
        mock_builder.build.return_value = Mock()
        
        # Mock tqdm
        mock_tqdm.return_value = mock_contacts
        mock_tqdm.write = Mock()
        
        with patch('src.main.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '2024-01-01 12:00:00'
            send_in_bulk()
        
        # Verify success rate calculation (1 success out of 2 = 50%)
        report_call = mock_generate_report.call_args
        assert report_call[1]['success_rate'] == 50.0
        assert report_call[1]['total_contacts'] == 2
        assert report_call[1]['successful_count'] == 1
        assert report_call[1]['failed_count'] == 1


class TestBlastApproval:
    """Test suite for blast approval functionality."""
    
    def test_display_blast_summary_shows_all_info(self, capsys):
        """Test that blast summary displays all required information."""
        from src.main import display_blast_summary
        
        contacts = [
            {
                'Email': 'test1@example.com',
                'Primary Contact Name': 'John Doe',
                'Entity Name': 'Test Company 1',
                'first_name': 'John'
            },
            {
                'Email': 'test2@example.com',
                'Primary Contact Name': 'Jane Smith',
                'Entity Name': 'Test Company 2',
                'first_name': 'Jane'
            }
        ]
        
        with patch('src.main.config', {'subject': 'Test Subject'}):
            with patch('os.getenv', return_value='sender@test.com'):
                display_blast_summary(contacts)
        
        captured = capsys.readouterr()
        # Strip ANSI color codes for easier testing
        import re
        output = re.sub(r'\x1b\[[0-9;]*m', '', captured.out)
        
        assert 'EMAIL BLAST SUMMARY' in output
        assert 'Total Contacts:' in output
        assert '2' in output
        assert 'Test Subject' in output
        assert 'sender@test.com' in output
        assert 'John Doe' in output
        assert 'Jane Smith' in output
    
    def test_display_blast_summary_preview_limit(self, capsys):
        """Test that blast summary shows only first 5 contacts."""
        from src.main import display_blast_summary
        
        contacts = [
            {
                'Email': f'test{i}@example.com',
                'Primary Contact Name': f'User {i}',
                'Entity Name': f'Company {i}',
                'first_name': f'User{i}'
            }
            for i in range(10)
        ]
        
        with patch('src.main.config', {'subject': 'Test Subject'}):
            with patch('os.getenv', return_value='sender@test.com'):
                display_blast_summary(contacts)
        
        captured = capsys.readouterr()
        assert 'and 5 more' in captured.out
        assert 'User 0' in captured.out  # First contact shown
        assert 'User 4' in captured.out  # 5th contact shown
    
    @patch('builtins.input', return_value='yes')
    @patch('src.main.logger')
    def test_request_blast_approval_user_approves(self, mock_logger, mock_input):
        """Test blast approval when user confirms."""
        from src.main import request_blast_approval
        
        contacts = [{'Email': 'test@example.com', 'Primary Contact Name': 'Test'}]
        
        with patch('src.main.display_blast_summary'):
            result = request_blast_approval(contacts)
        
        assert result is True
        mock_logger.info.assert_called_once()
        assert 'approved' in mock_logger.info.call_args[0][0].lower()
    
    @patch('builtins.input', return_value='no')
    @patch('src.main.logger')
    def test_request_blast_approval_user_rejects(self, mock_logger, mock_input):
        """Test blast approval when user rejects."""
        from src.main import request_blast_approval
        
        contacts = [{'Email': 'test@example.com', 'Primary Contact Name': 'Test'}]
        
        with patch('src.main.display_blast_summary'):
            result = request_blast_approval(contacts)
        
        assert result is False
        mock_logger.warning.assert_called_once()
        assert 'cancelled' in mock_logger.warning.call_args[0][0].lower()
    
    @patch('builtins.input', side_effect=['invalid', 'maybe', 'yes'])
    @patch('src.main.logger')
    def test_request_blast_approval_invalid_input_retry(self, mock_logger, mock_input, capsys):
        """Test blast approval handles invalid input and retries."""
        from src.main import request_blast_approval
        
        contacts = [{'Email': 'test@example.com', 'Primary Contact Name': 'Test'}]
        
        with patch('src.main.display_blast_summary'):
            result = request_blast_approval(contacts)
        
        assert result is True
        assert mock_input.call_count == 3  # Called 3 times due to invalid inputs
        
        captured = capsys.readouterr()
        assert 'Invalid input' in captured.out
    
    @patch('builtins.input', return_value='y')
    @patch('src.main.logger')
    def test_request_blast_approval_shorthand_yes(self, mock_logger, mock_input):
        """Test blast approval accepts 'y' as yes."""
        from src.main import request_blast_approval
        
        contacts = [{'Email': 'test@example.com', 'Primary Contact Name': 'Test'}]
        
        with patch('src.main.display_blast_summary'):
            result = request_blast_approval(contacts)
        
        assert result is True
    
    @patch('builtins.input', return_value='n')
    @patch('src.main.logger')
    def test_request_blast_approval_shorthand_no(self, mock_logger, mock_input):
        """Test blast approval accepts 'n' as no."""
        from src.main import request_blast_approval
        
        contacts = [{'Email': 'test@example.com', 'Primary Contact Name': 'Test'}]
        
        with patch('src.main.display_blast_summary'):
            result = request_blast_approval(contacts)
        
        assert result is False
    
    @patch('src.main.request_blast_approval', return_value=False)
    @patch('src.main.parse_contacts_from_csv')
    @patch('src.main.MailerSendClient')
    @patch('src.main.logger')
    def test_send_in_bulk_aborts_without_approval(self, mock_logger, mock_client, 
                                                   mock_parse, mock_approval):
        """Test that send_in_bulk aborts when approval is denied."""
        from src.main import send_in_bulk
        
        mock_contacts = [{'Email': 'test@example.com', 'first_name': 'Test'}]
        mock_parse.return_value = mock_contacts
        
        send_in_bulk()
        
        # Verify approval was requested
        mock_approval.assert_called_once_with(mock_contacts)
        
        # Verify no emails were sent
        mock_client.return_value.emails.send.assert_not_called()
        
        # Verify abort logging
        abort_calls = [call for call in mock_logger.info.call_args_list 
                      if 'aborted' in str(call).lower()]
        assert len(abort_calls) > 0
    
    @patch('src.main.generate_email_summary_report')
    @patch('src.main.log_successful_emails')
    @patch('src.main.log_failed_emails')
    @patch('src.main.time.sleep')
    @patch('src.main.tqdm')
    @patch('src.main.request_blast_approval', return_value=True)
    @patch('src.main.parse_contacts_from_csv')
    @patch('src.main.load_email_config')
    @patch('src.main.EmailBuilder')
    @patch('src.main.MailerSendClient')
    @patch('src.main.logger')
    @patch('os.getenv')
    def test_send_in_bulk_proceeds_with_approval(self, mock_getenv, mock_logger, mock_client,
                                                 mock_builder_cls, mock_config, mock_parse,
                                                 mock_approval, mock_tqdm, mock_sleep,
                                                 mock_log_failed, mock_log_success, mock_report):
        """Test that send_in_bulk proceeds when approval is granted."""
        from src.main import send_in_bulk
        
        # Setup mocks
        mock_getenv.side_effect = lambda key: {
            'TIERII_MAILERSEND_API_TOKEN': 'test_token',
            'TIERII_SENDER_EMAIL': 'sender@test.com'
        }.get(key)
        
        mock_config.return_value = {
            'subject': 'Test',
            'body': 'Hello {name}',
            'html_content': '<p>Hello {name}</p>'
        }
        
        mock_contacts = [
            {'Email': 'test@example.com', 'Primary Contact Name': 'Test', 'first_name': 'Test'}
        ]
        mock_parse.return_value = mock_contacts
        
        # Mock email builder
        mock_builder = Mock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.from_email.return_value = mock_builder
        mock_builder.to_many.return_value = mock_builder
        mock_builder.subject.return_value = mock_builder
        mock_builder.html.return_value = mock_builder
        mock_builder.text.return_value = mock_builder
        mock_builder.build.return_value = Mock()
        
        # Mock successful response
        mock_response = Mock(status_code=202)
        mock_client.return_value.emails.send.return_value = mock_response
        
        # Mock tqdm
        mock_tqdm.return_value = mock_contacts
        mock_tqdm.write = Mock()
        
        send_in_bulk()
        
        # Verify approval was requested
        mock_approval.assert_called_once_with(mock_contacts)
        
        # Verify emails were sent
        mock_client.return_value.emails.send.assert_called_once()
    
    def test_display_blast_summary_empty_contacts(self, capsys):
        """Test blast summary with empty contact list."""
        from src.main import display_blast_summary
        
        with patch('src.main.config', {'subject': 'Test Subject'}):
            with patch('os.getenv', return_value='sender@test.com'):
                display_blast_summary([])
        
        captured = capsys.readouterr()
        # Strip ANSI color codes for easier testing
        import re
        output = re.sub(r'\x1b\[[0-9;]*m', '', captured.out)
        
        assert 'Total Contacts:' in output
        assert '0' in output


class TestMainModuleIntegration:
    """Integration tests for main module functionality."""
    
    @patch('src.main.send_in_bulk')
    def test_main_execution(self, mock_send_in_bulk):
        """Test main module execution."""
        # Import and test main execution
        import src.main
        
        # Verify that if __name__ == "__main__" would call send_in_bulk
        # This tests the module structure without actually running it
        assert hasattr(src.main, 'send_in_bulk')
        assert callable(src.main.send_in_bulk)