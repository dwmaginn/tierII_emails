"""Comprehensive tests for email retry logic and exponential backoff.

This module tests the retry mechanism in the send_email() function from email_campaign.py,
covering network failure scenarios, authentication token refresh during retries,
exponential backoff timing, and various error conditions.
"""

import pytest
import time
from unittest.mock import patch, Mock, MagicMock, call
from datetime import datetime, timedelta

# Import the function under test and related exceptions
from src.email_campaign import send_email
from src.auth.base_authentication_manager import (
    AuthenticationError,
    NetworkError,
    InvalidCredentialsError
)


class TestEmailRetryLogic:
    """Test suite for email retry logic and exponential backoff."""

    @pytest.fixture
    def mock_auth_manager(self):
        """Mock authentication manager for testing."""
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        return mock_manager

    @pytest.fixture
    def mock_load_email_template(self):
        """Mock email template loading."""
        with patch('src.email_campaign.load_email_template') as mock_template:
            mock_template.return_value = "<html><body>Hello {first_name}!</body></html>"
            yield mock_template

    @pytest.fixture
    def mock_get_first_name(self):
        """Mock first name processing."""
        with patch('src.email_campaign.get_first_name') as mock_name:
            mock_name.return_value = "TestUser"
            yield mock_name

    def test_send_email_success_first_attempt(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test successful email sending on first attempt (no retries needed)."""
        with patch('src.email_campaign.auth_manager', mock_auth_manager):
            result = send_email("test@example.com", "TestUser")
        
        assert result is True
        mock_auth_manager.send_email.assert_called_once()
        mock_load_email_template.assert_called_once_with("TestUser")

    def test_send_email_authentication_error_retry_success(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test retry logic with authentication error followed by success."""
        # First call fails with AuthenticationError, second succeeds
        mock_auth_manager.send_email.side_effect = [
            AuthenticationError("Token expired", None, "TOKEN_EXPIRED"),
            True
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager), \
             patch('time.sleep') as mock_sleep:
            result = send_email("test@example.com", "TestUser")
        
        assert result is True
        assert mock_auth_manager.send_email.call_count == 2
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1 second backoff

    def test_send_email_network_error_retry_success(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test retry logic with network error followed by success."""
        # First call fails with NetworkError, second succeeds
        mock_auth_manager.send_email.side_effect = [
            NetworkError("Connection timeout", None, "TIMEOUT"),
            True
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager), \
             patch('time.sleep') as mock_sleep:
            result = send_email("test@example.com", "TestUser")
        
        assert result is True
        assert mock_auth_manager.send_email.call_count == 2
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1 second backoff

    def test_send_email_exponential_backoff_timing(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test exponential backoff timing progression."""
        # All attempts fail except the last one
        mock_auth_manager.send_email.side_effect = [
            AuthenticationError("Error 1", None, "ERROR_1"),
            NetworkError("Error 2", None, "ERROR_2"),
            True  # Third attempt succeeds
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager), \
             patch('time.sleep') as mock_sleep:
            result = send_email("test@example.com", "TestUser")
        
        assert result is True
        assert mock_auth_manager.send_email.call_count == 3
        
        # Check exponential backoff: 2^0=1, 2^1=2
        expected_calls = [call(1), call(2)]
        mock_sleep.assert_has_calls(expected_calls)

    def test_send_email_max_retries_exceeded(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test behavior when maximum retries are exceeded."""
        # All attempts fail
        mock_auth_manager.send_email.side_effect = [
            AuthenticationError("Error 1", None, "ERROR_1"),
            NetworkError("Error 2", None, "ERROR_2"),
            AuthenticationError("Error 3", None, "ERROR_3")
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager), \
             patch('time.sleep') as mock_sleep:
            result = send_email("test@example.com", "TestUser", max_retries=3)
        
        assert result is False
        assert mock_auth_manager.send_email.call_count == 3
        
        # Check all backoff attempts: 2^0=1, 2^1=2
        expected_calls = [call(1), call(2)]
        mock_sleep.assert_has_calls(expected_calls)

    def test_send_email_custom_max_retries(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test custom maximum retry count."""
        # All attempts fail
        mock_auth_manager.send_email.side_effect = [
            AuthenticationError("Error 1", None, "ERROR_1"),
            NetworkError("Error 2", None, "ERROR_2"),
            AuthenticationError("Error 3", None, "ERROR_3"),
            NetworkError("Error 4", None, "ERROR_4"),
            True  # Fifth attempt succeeds
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager), \
             patch('time.sleep') as mock_sleep:
            result = send_email("test@example.com", "TestUser", max_retries=5)
        
        assert result is True
        assert mock_auth_manager.send_email.call_count == 5
        
        # Check exponential backoff: 2^0=1, 2^1=2, 2^2=4, 2^3=8
        expected_calls = [call(1), call(2), call(4), call(8)]
        mock_sleep.assert_has_calls(expected_calls)

    def test_send_email_unexpected_exception_retry(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test retry logic with unexpected exceptions."""
        # First call fails with unexpected exception, second succeeds
        mock_auth_manager.send_email.side_effect = [
            ValueError("Unexpected error"),
            True
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager), \
             patch('time.sleep') as mock_sleep:
            result = send_email("test@example.com", "TestUser")
        
        assert result is True
        assert mock_auth_manager.send_email.call_count == 2
        mock_sleep.assert_called_once_with(1)

    def test_send_email_no_auth_manager_no_retry(self, mock_load_email_template, mock_get_first_name):
        """Test that retries occur even when auth manager is None (raises AuthenticationError)."""
        with patch('src.email_campaign.auth_manager', None), \
             patch('time.sleep') as mock_sleep:
            result = send_email("test@example.com", "TestUser")
        
        assert result is False
        # Should retry because None auth_manager raises AuthenticationError which triggers retry
        assert mock_sleep.call_count == 2  # max_retries=3, so 2 sleep calls

    def test_send_email_template_loading_error_retry(self, mock_auth_manager, mock_get_first_name):
        """Test retry behavior when template loading fails."""
        with patch('src.email_campaign.load_email_template') as mock_template:
            # Template loading fails first time, succeeds second time
            mock_template.side_effect = [
                IOError("Template file not found"),
                "<html><body>Hello TestUser!</body></html>"
            ]
            
            with patch('src.email_campaign.auth_manager', mock_auth_manager), \
                 patch('time.sleep') as mock_sleep:
                result = send_email("test@example.com", "TestUser")
        
        assert result is True
        assert mock_template.call_count == 2
        mock_sleep.assert_called_once_with(1)

    def test_send_email_mixed_error_types_retry(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test retry logic with mixed error types."""
        mock_auth_manager.send_email.side_effect = [
            AuthenticationError("Auth error", None, "AUTH_ERROR"),
            NetworkError("Network error", None, "NETWORK_ERROR"),
            ValueError("Unexpected error"),
            True  # Fourth attempt succeeds
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager), \
             patch('time.sleep') as mock_sleep:
            result = send_email("test@example.com", "TestUser", max_retries=4)
        
        assert result is True
        assert mock_auth_manager.send_email.call_count == 4
        
        # Check exponential backoff: 2^0=1, 2^1=2, 2^2=4
        expected_calls = [call(1), call(2), call(4)]
        mock_sleep.assert_has_calls(expected_calls)

    def test_send_email_retry_timing_accuracy(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test that retry timing follows exponential backoff accurately."""
        mock_auth_manager.send_email.side_effect = [
            AuthenticationError("Error", None, "ERROR"),
            AuthenticationError("Error", None, "ERROR"),
            AuthenticationError("Error", None, "ERROR")
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager):
            start_time = time.time()
            
            with patch('time.sleep') as mock_sleep:
                result = send_email("test@example.com", "TestUser", max_retries=3)
            
            # Verify exact sleep durations
            expected_sleeps = [1, 2]  # 2^0, 2^1
            actual_sleeps = [call_args[0][0] for call_args in mock_sleep.call_args_list]
            assert actual_sleeps == expected_sleeps

    def test_send_email_concurrent_retry_scenarios(self, mock_load_email_template, mock_get_first_name):
        """Test retry logic under simulated concurrent scenarios."""
        # Simulate multiple concurrent email sends with different retry patterns
        scenarios = [
            [AuthenticationError("Auth", None, "AUTH"), True],  # 1 retry
            [NetworkError("Net", None, "NET"), NetworkError("Net", None, "NET"), True],  # 2 retries
            [ValueError("Val"), True],  # 1 retry with unexpected error
        ]
        
        results = []
        for scenario in scenarios:
            mock_auth_manager = Mock()
            mock_auth_manager.send_email.side_effect = scenario
            
            with patch('src.email_campaign.auth_manager', mock_auth_manager), \
                 patch('time.sleep'):
                result = send_email("test@example.com", "TestUser")
                results.append(result)
        
        # All scenarios should eventually succeed
        assert all(results)

    def test_send_email_retry_with_different_recipients(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test retry logic with different recipient emails."""
        # Test that retry logic works consistently across different recipients
        recipients = ["user1@example.com", "user2@company.org", "user3@domain.net"]
        
        for recipient in recipients:
            mock_auth_manager.send_email.side_effect = [
                NetworkError("Network error", None, "NETWORK"),
                True
            ]
            
            with patch('src.email_campaign.auth_manager', mock_auth_manager), \
                 patch('time.sleep') as mock_sleep:
                result = send_email(recipient, "TestUser")
            
            assert result is True
            mock_sleep.assert_called_with(1)
            mock_sleep.reset_mock()
            mock_auth_manager.reset_mock()

    def test_send_email_retry_preserves_email_content(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test that email content is preserved across retry attempts."""
        expected_content = "<html><body>Hello TestUser!</body></html>"
        mock_load_email_template.return_value = expected_content
        
        mock_auth_manager.send_email.side_effect = [
            AuthenticationError("Auth error", None, "AUTH"),
            True
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager), \
             patch('time.sleep'):
            result = send_email("test@example.com", "TestUser")
        
        assert result is True
        
        # Verify that the same content was used in both attempts
        calls = mock_auth_manager.send_email.call_args_list
        assert len(calls) == 2
        
        # Both calls should have the same parameters
        for call_args in calls:
            args, kwargs = call_args
            assert kwargs['html_content'] == expected_content

    def test_send_email_retry_backoff_maximum_limit(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test exponential backoff with many retries to verify maximum limits."""
        # Create a scenario with many failures
        failures = [AuthenticationError("Error", None, "ERROR")] * 10
        mock_auth_manager.send_email.side_effect = failures
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager), \
             patch('time.sleep') as mock_sleep:
            result = send_email("test@example.com", "TestUser", max_retries=10)
        
        assert result is False
        
        # Check that exponential backoff was applied correctly
        expected_sleeps = [2**i for i in range(9)]  # 2^0 to 2^8
        actual_sleeps = [call_args[0][0] for call_args in mock_sleep.call_args_list]
        assert actual_sleeps == expected_sleeps

    def test_send_email_retry_state_isolation(self, mock_load_email_template, mock_get_first_name):
        """Test that retry state is isolated between different email sends."""
        # First email send with retries
        mock_auth_manager1 = Mock()
        mock_auth_manager1.send_email.side_effect = [
            AuthenticationError("Error", None, "ERROR"),
            AuthenticationError("Error", None, "ERROR"),
            True
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager1), \
             patch('time.sleep') as mock_sleep1:
            result1 = send_email("test1@example.com", "User1")
        
        # Second email send should start fresh (no retry state carryover)
        mock_auth_manager2 = Mock()
        mock_auth_manager2.send_email.side_effect = [
            NetworkError("Error", None, "ERROR"),
            True
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager2), \
             patch('time.sleep') as mock_sleep2:
            result2 = send_email("test2@example.com", "User2")
        
        assert result1 is True
        assert result2 is True
        
        # First send should have 2 sleep calls (2 retries)
        assert len(mock_sleep1.call_args_list) == 2
        # Second send should have 1 sleep call (1 retry)
        assert len(mock_sleep2.call_args_list) == 1
        
        # Second send should start with 1-second backoff, not continue from first send
        assert mock_sleep2.call_args_list[0][0][0] == 1

    def test_send_email_retry_error_logging(self, mock_auth_manager, mock_load_email_template, mock_get_first_name):
        """Test that retry attempts are properly logged."""
        mock_auth_manager.send_email.side_effect = [
            AuthenticationError("Auth failed", None, "AUTH_FAILED"),
            NetworkError("Network timeout", None, "TIMEOUT"),
            True
        ]
        
        with patch('src.email_campaign.auth_manager', mock_auth_manager), \
             patch('time.sleep'), \
             patch('builtins.print') as mock_print:
            result = send_email("test@example.com", "TestUser")
        
        assert result is True
        
        # Verify that print was called (indicating logging occurred)
        assert mock_print.call_count >= 3  # At least 2 errors + 1 success
        
        # Check that some error logging occurred
        print_calls = [str(call) for call in mock_print.call_args_list]
        has_error_logging = any("error" in call.lower() for call in print_calls)
        has_success_logging = any("sent" in call.lower() for call in print_calls)
        
        assert has_error_logging
        assert has_success_logging