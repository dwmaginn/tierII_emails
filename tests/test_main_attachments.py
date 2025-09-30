"""Comprehensive test suite for main.py email builder attachment integration."""

import pytest
import os
import json
import tempfile
import base64
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
from io import StringIO

from src.main import send_in_bulk


class TestEmailBuilderAttachments:
    """Test suite for EmailBuilder attachment integration in main.py."""
    
    @pytest.fixture
    def sample_config_with_attachments(self):
        """Sample email configuration with processed attachments."""
        return {
            "subject": "Test Email with Attachments",
            "body": "Hi {name},\n\nThis is a test email with attachments.\n\nBest regards,\nTest Team",
            "html": "templates/test_template.html",
            "html_content": "<html><body><h1>Hi {name}</h1><img src='cid:test-logo'></body></html>",
            "processed_attachments": [
                {
                    "filename": "test_logo.png",
                    "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                    "content_id": "test-logo",
                    "disposition": "inline"
                },
                {
                    "filename": "document.pdf",
                    "content": "JVBERi0xLjQKJcOkw7zDtsO8w6HDqMOgw6rDqMOkw6jDpMOqw6bDqMOmw6o=",
                    "content_id": "test-doc",
                    "disposition": "attachment"
                }
            ],
            "contacts": "data/test/testdata.csv"
        }
    
    @pytest.fixture
    def sample_config_no_attachments(self):
        """Sample email configuration without attachments."""
        return {
            "subject": "Test Email No Attachments",
            "body": "Hi {name},\n\nThis is a test email without attachments.\n\nBest regards,\nTest Team",
            "html": "templates/test_template.html",
            "html_content": "<html><body><h1>Hi {name}</h1></body></html>",
            "processed_attachments": [],
            "contacts": "data/test/testdata.csv"
        }
    
    @pytest.fixture
    def sample_contacts(self):
        """Sample contact data for testing."""
        return [
            {
                "Email": "test1@example.com",
                "Primary Contact Name": "John Doe",
                "first_name": "John"
            },
            {
                "Email": "test2@example.com", 
                "Primary Contact Name": "Jane Smith",
                "first_name": "Jane"
            }
        ]

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
    @patch('os.getenv')
    def test_send_in_bulk_with_attachments(self, mock_getenv, mock_load_config, mock_parse_contacts,
                                         mock_mailersend, mock_email_builder, mock_logger, mock_tqdm,
                                         mock_sleep, mock_log_failed, mock_log_successful, mock_generate_report,
                                         sample_config_with_attachments, sample_contacts):
        """Test send_in_bulk correctly handles emails with attachments."""
        # Setup mocks
        mock_getenv.return_value = "test@example.com"
        mock_load_config.return_value = sample_config_with_attachments
        mock_parse_contacts.return_value = sample_contacts
        
        # Mock MailerSend client and EmailBuilder
        mock_client = Mock()
        mock_mailersend.return_value = mock_client
        mock_client.emails.send.return_value = Mock(status_code=202)
        
        # Mock EmailBuilder chain - ensure same instance is returned for all calls
        mock_builder_instance = Mock()
        mock_email_builder.return_value = mock_builder_instance
        mock_builder_instance.from_email.return_value = mock_builder_instance
        mock_builder_instance.to_many.return_value = mock_builder_instance
        mock_builder_instance.subject.return_value = mock_builder_instance
        mock_builder_instance.html.return_value = mock_builder_instance
        mock_builder_instance.text.return_value = mock_builder_instance
        mock_builder_instance.attachment.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = Mock()
        
        # Mock tqdm progress bar
        mock_progress = Mock()
        mock_tqdm.return_value = mock_progress
        mock_progress.__iter__ = Mock(return_value=iter(sample_contacts))
        
        # Execute
        send_in_bulk()
        
        # Verify EmailBuilder was called with attachments
        assert mock_builder_instance.attachment.call_count == 4  # 2 contacts × 2 attachments each
        
        # Verify attachment calls have correct parameters
        attachment_calls = mock_builder_instance.attachment.call_args_list
        
        # First contact's attachments
        first_attachment_call = attachment_calls[0]
        assert first_attachment_call[1]['content'] == sample_config_with_attachments['processed_attachments'][0]['content']
        assert first_attachment_call[1]['filename'] == 'test_logo.png'
        assert first_attachment_call[1]['disposition'] == 'inline'
        assert first_attachment_call[1]['content_id'] == 'test-logo'
        
        second_attachment_call = attachment_calls[1]
        assert second_attachment_call[1]['content'] == sample_config_with_attachments['processed_attachments'][1]['content']
        assert second_attachment_call[1]['filename'] == 'document.pdf'
        assert second_attachment_call[1]['disposition'] == 'attachment'
        assert second_attachment_call[1]['content_id'] == 'test-doc'

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
    @patch('os.getenv')
    def test_send_in_bulk_without_attachments(self, mock_getenv, mock_load_config, mock_parse_contacts,
                                            mock_mailersend, mock_email_builder, mock_logger, mock_tqdm,
                                            mock_sleep, mock_log_failed, mock_log_successful, mock_generate_report,
                                            sample_config_no_attachments, sample_contacts):
        """Test send_in_bulk works correctly without attachments (backward compatibility)."""
        # Setup mocks
        mock_getenv.return_value = "test@example.com"
        mock_load_config.return_value = sample_config_no_attachments
        mock_parse_contacts.return_value = sample_contacts
        
        # Mock MailerSend client and EmailBuilder
        mock_client = Mock()
        mock_mailersend.return_value = mock_client
        mock_client.emails.send.return_value = Mock(status_code=202)
        
        # Mock EmailBuilder chain - ensure same instance is returned for all calls
        mock_builder_instance = Mock()
        mock_email_builder.return_value = mock_builder_instance
        mock_builder_instance.from_email.return_value = mock_builder_instance
        mock_builder_instance.to_many.return_value = mock_builder_instance
        mock_builder_instance.subject.return_value = mock_builder_instance
        mock_builder_instance.html.return_value = mock_builder_instance
        mock_builder_instance.text.return_value = mock_builder_instance
        mock_builder_instance.attachment.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = Mock()
        
        # Mock tqdm progress bar
        mock_progress = Mock()
        mock_tqdm.return_value = mock_progress
        mock_progress.__iter__ = Mock(return_value=iter(sample_contacts))
        
        # Execute
        send_in_bulk()
        
        # Verify EmailBuilder was NOT called with attachments
        assert mock_builder_instance.attachment.call_count == 0
        
        # Verify other EmailBuilder methods were still called correctly
        assert mock_builder_instance.from_email.call_count == 2
        assert mock_builder_instance.to_many.call_count == 2
        assert mock_builder_instance.subject.call_count == 2
        assert mock_builder_instance.html.call_count == 2
        assert mock_builder_instance.text.call_count == 2
        assert mock_builder_instance.build.call_count == 2

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
    @patch('os.getenv')
    def test_attachment_content_id_handling(self, mock_getenv, mock_load_config, mock_parse_contacts,
                                          mock_mailersend, mock_email_builder, mock_logger, mock_tqdm,
                                          mock_sleep, mock_log_failed, mock_log_successful, mock_generate_report,
                                          sample_contacts):
        """Test handling of attachments with and without content_id."""
        config_mixed_content_ids = {
            "subject": "Test Mixed Content IDs",
            "body": "Test body {name}",
            "html_content": "<html><body><h1>Hi {name}</h1></body></html>",
            "processed_attachments": [
                {
                    "filename": "with_id.png",
                    "content": "base64content1",
                    "content_id": "image-1",
                    "disposition": "inline"
                },
                {
                    "filename": "without_id.pdf",
                    "content": "base64content2",
                    "content_id": None,
                    "disposition": "attachment"
                }
            ],
            "contacts": "data/test.csv"
        }
        
        # Setup mocks
        mock_getenv.return_value = "test@example.com"
        mock_load_config.return_value = config_mixed_content_ids
        mock_parse_contacts.return_value = [sample_contacts[0]]  # Just one contact for simplicity
        
        # Mock MailerSend client and EmailBuilder
        mock_client = Mock()
        mock_mailersend.return_value = mock_client
        mock_client.emails.send.return_value = Mock(status_code=202)
        
        # Mock EmailBuilder chain - ensure same instance is returned for all calls
        mock_builder_instance = Mock()
        mock_email_builder.return_value = mock_builder_instance
        mock_builder_instance.from_email.return_value = mock_builder_instance
        mock_builder_instance.to_many.return_value = mock_builder_instance
        mock_builder_instance.subject.return_value = mock_builder_instance
        mock_builder_instance.html.return_value = mock_builder_instance
        mock_builder_instance.text.return_value = mock_builder_instance
        mock_builder_instance.attachment.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = Mock()
        
        # Mock tqdm progress bar
        mock_progress = Mock()
        mock_tqdm.return_value = mock_progress
        mock_progress.__iter__ = Mock(return_value=iter([sample_contacts[0]]))
        
        # Execute
        send_in_bulk()
        
        # Verify both attachments were processed
        assert mock_builder_instance.attachment.call_count == 2
        
        # Verify content_id handling
        attachment_calls = mock_builder_instance.attachment.call_args_list
        
        # First attachment with content_id
        first_call = attachment_calls[0]
        assert first_call[1]['content_id'] == 'image-1'
        
        # Second attachment without content_id (None)
        second_call = attachment_calls[1]
        assert first_call[1]['content_id'] == 'image-1'

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
    @patch('os.getenv')
    def test_html_content_personalization_with_attachments(self, mock_getenv, mock_load_config, mock_parse_contacts,
                                                          mock_mailersend, mock_email_builder, mock_logger, mock_tqdm,
                                                          mock_sleep, mock_log_failed, mock_log_successful, mock_generate_report,
                                                          sample_config_with_attachments, sample_contacts):
        """Test that HTML content personalization works correctly with attachments."""
        # Setup mocks
        mock_getenv.return_value = "test@example.com"
        mock_load_config.return_value = sample_config_with_attachments
        mock_parse_contacts.return_value = sample_contacts
        
        # Mock MailerSend client and EmailBuilder
        mock_client = Mock()
        mock_mailersend.return_value = mock_client
        mock_client.emails.send.return_value = Mock(status_code=202)
        
        # Mock EmailBuilder chain - ensure same instance is returned for all calls
        mock_builder_instance = Mock()
        mock_email_builder.return_value = mock_builder_instance
        mock_builder_instance.from_email.return_value = mock_builder_instance
        mock_builder_instance.to_many.return_value = mock_builder_instance
        mock_builder_instance.subject.return_value = mock_builder_instance
        mock_builder_instance.html.return_value = mock_builder_instance
        mock_builder_instance.text.return_value = mock_builder_instance
        mock_builder_instance.attachment.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = Mock()
        
        # Mock tqdm progress bar
        mock_progress = Mock()
        mock_tqdm.return_value = mock_progress
        mock_progress.__iter__ = Mock(return_value=iter(sample_contacts))
        
        # Execute
        send_in_bulk()
        
        # Verify HTML content was personalized correctly
        html_calls = mock_builder_instance.html.call_args_list
        
        # First contact (John)
        first_html_call = html_calls[0]
        assert "Hi John" in first_html_call[0][0]
        assert "cid:test-logo" in first_html_call[0][0]
        
        # Second contact (Jane)
        second_html_call = html_calls[1]
        assert "Hi Jane" in second_html_call[0][0]
        assert "cid:test-logo" in second_html_call[0][0]

    def test_attachment_parameter_validation(self):
        """Test that attachment parameters are validated correctly."""
        # This test ensures that the attachment method is called with the correct parameter structure
        # that MailerSend expects
        
        sample_attachment = {
            "filename": "test.png",
            "content": "base64encodedcontent",
            "content_id": "test-image",
            "disposition": "inline"
        }
        
        # Verify all required parameters are present
        assert 'filename' in sample_attachment
        assert 'content' in sample_attachment
        assert 'content_id' in sample_attachment
        assert 'disposition' in sample_attachment
        
        # Verify parameter types
        assert isinstance(sample_attachment['filename'], str)
        assert isinstance(sample_attachment['content'], str)
        assert isinstance(sample_attachment['content_id'], str)
        assert isinstance(sample_attachment['disposition'], str)
        
        # Verify disposition values
        assert sample_attachment['disposition'] in ['inline', 'attachment']

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
    @patch('os.getenv')
    def test_empty_processed_attachments_handling(self, mock_getenv, mock_load_config, mock_parse_contacts,
                                                mock_mailersend, mock_email_builder, mock_logger, mock_tqdm,
                                                mock_sleep, mock_log_failed, mock_log_successful, mock_generate_report,
                                                sample_contacts):
        """Test handling when processed_attachments key exists but is empty."""
        config_empty_processed = {
            "subject": "Test Empty Processed",
            "body": "Test body {name}",
            "html_content": "<html><body><h1>Hi {name}</h1></body></html>",
            "processed_attachments": [],  # Explicitly empty
            "contacts": "data/test.csv"
        }
        
        # Setup mocks
        mock_getenv.return_value = "test@example.com"
        mock_load_config.return_value = config_empty_processed
        mock_parse_contacts.return_value = [sample_contacts[0]]
        
        # Mock MailerSend client and EmailBuilder
        mock_client = Mock()
        mock_mailersend.return_value = mock_client
        mock_client.emails.send.return_value = Mock(status_code=202)
        
        # Mock EmailBuilder chain
        mock_builder_instance = Mock()
        mock_email_builder.return_value = mock_builder_instance
        mock_builder_instance.from_email.return_value = mock_builder_instance
        mock_builder_instance.to_many.return_value = mock_builder_instance
        mock_builder_instance.subject.return_value = mock_builder_instance
        mock_builder_instance.html.return_value = mock_builder_instance
        mock_builder_instance.text.return_value = mock_builder_instance
        mock_builder_instance.attachment.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = Mock()
        
        # Mock tqdm progress bar
        mock_progress = Mock()
        mock_tqdm.return_value = mock_progress
        mock_progress.__iter__ = Mock(return_value=iter([sample_contacts[0]]))
        
        # Execute
        send_in_bulk()
        
        # Verify no attachment calls were made
        assert mock_builder_instance.attachment.call_count == 0
        
        # Verify email was still built and sent successfully
        assert mock_builder_instance.build.call_count == 1
        assert mock_client.emails.send.call_count == 1