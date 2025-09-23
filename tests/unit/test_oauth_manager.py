"""Unit tests for OAuthTokenManager class.

Tests OAuth token acquisition, refresh, expiry handling, and error scenarios.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import requests
import sys
import os

# Add src to path for imports
src_path = os.path.join(os.path.dirname(__file__), "..", "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


class TestOAuthTokenManager:
    """Test cases for OAuthTokenManager class."""

    @pytest.fixture
    def token_manager(self):
        """Create a fresh OAuthTokenManager instance for each test."""
        with patch.dict(
            "sys.modules",
            {
                "config": Mock(
                    TENANT_ID="12345678-1234-1234-1234-123456789abc",
                    CLIENT_ID="87654321-4321-4321-4321-cba987654321",
                    CLIENT_SECRET="test-client-secret",
                )
            },
        ):
            from email_campaign import OAuthTokenManager

            return OAuthTokenManager()

    @pytest.fixture
    def mock_successful_response(self):
        """Mock successful OAuth response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "access_token": "mock_access_token_12345",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "https://outlook.office365.com/.default",
        }
        return mock_response

    @pytest.fixture
    def mock_error_response(self):
        """Mock error OAuth response."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "401 Unauthorized"
        )
        return mock_response

    @pytest.mark.oauth
    @pytest.mark.unit
    def test_oauth_manager_initialization(self, token_manager):
        """Test OAuthTokenManager initialization."""
        assert token_manager.access_token is None
        assert token_manager.token_expiry is None
        assert token_manager.scope == "https://outlook.office365.com/.default"

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_get_access_token_success(
        self, mock_post, token_manager, mock_successful_response
    ):
        """Test successful token acquisition."""
        # Setup requests mock
        mock_post.return_value = mock_successful_response

        # Test token acquisition with frozen time
        from freezegun import freeze_time
        from datetime import datetime, timedelta

        with freeze_time("2024-01-01 12:00:00"):
            token = token_manager.get_access_token()

            # Assertions
            assert token == "mock_access_token_12345"
            assert token_manager.access_token == "mock_access_token_12345"

            # Verify token expiry is set correctly (3600 - 300 = 3300 seconds from frozen time)
            frozen_time = (
                datetime.now()
            )  # Use datetime.now() to get FakeDatetime object
            expected_expiry = frozen_time + timedelta(seconds=3300)
            assert token_manager.token_expiry == expected_expiry

        # Verify correct API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert (
            "https://login.microsoftonline.com/12345678-1234-1234-1234-123456789abc/oauth2/v2.0/token"
            in call_args[0][0]
        )

        expected_data = {
            "client_id": "87654321-4321-4321-4321-cba987654321",
            "client_secret": "test-client-secret",
            "scope": "https://outlook.office365.com/.default",
            "grant_type": "client_credentials",
        }
        assert call_args[1]["data"] == expected_data

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_get_access_token_uses_cached_token(
        self, mock_post, token_manager, freeze_time_fixture
    ):
        """Test that cached token is used when still valid."""
        from datetime import datetime, timedelta

        # Set up existing valid token
        token_manager.access_token = "cached_token_12345"
        token_manager.token_expiry = datetime.now() + timedelta(
            minutes=30
        )  # Valid for 30 more minutes

        # Get token
        token = token_manager.get_access_token()

        # Should return cached token without making HTTP request
        assert token == "cached_token_12345"
        mock_post.assert_not_called()

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_get_access_token_refreshes_expired_token(
        self, mock_post, token_manager, mock_successful_response, freeze_time_fixture
    ):
        """Test that expired token is refreshed."""
        from datetime import datetime, timedelta

        # Set up expired token
        token_manager.access_token = "expired_token"
        token_manager.token_expiry = datetime.now() - timedelta(
            minutes=5
        )  # Expired 5 minutes ago

        # Setup requests mock
        mock_post.return_value = mock_successful_response

        # Get token
        token = token_manager.get_access_token()

        # Should get new token
        assert token == "mock_access_token_12345"
        assert token_manager.access_token == "mock_access_token_12345"
        mock_post.assert_called_once()

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_get_access_token_http_error(
        self, mock_post, token_manager, mock_error_response
    ):
        """Test handling of HTTP errors during token acquisition."""
        mock_post.return_value = mock_error_response

        with pytest.raises(requests.exceptions.HTTPError):
            token_manager.get_access_token()

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_get_access_token_connection_error(self, mock_post, token_manager):
        """Test handling of connection errors during token acquisition."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(requests.exceptions.ConnectionError):
            token_manager.get_access_token()

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_get_access_token_timeout_error(self, mock_post, token_manager):
        """Test handling of timeout errors during token acquisition."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(requests.exceptions.Timeout):
            token_manager.get_access_token()

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_get_access_token_custom_expires_in(
        self, mock_post, token_manager, freeze_time_fixture
    ):
        """Test token acquisition with custom expires_in value."""
        # Setup response with custom expires_in
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "access_token": "custom_token",
            "expires_in": 7200,  # 2 hours
        }
        mock_post.return_value = mock_response

        # Get token
        token = token_manager.get_access_token()

        # Verify expiry calculation (7200 - 300 = 6900 seconds)
        from datetime import timedelta

        expected_expiry = datetime.now() + timedelta(seconds=6900)
        assert token_manager.token_expiry == expected_expiry

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_get_access_token_missing_expires_in(
        self, mock_post, token_manager, freeze_time_fixture
    ):
        """Test token acquisition when expires_in is missing from response."""
        # Setup response without expires_in
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"access_token": "token_without_expiry"}
        mock_post.return_value = mock_response

        # Get token
        token = token_manager.get_access_token()

        # Should use default 3600 seconds (3600 - 300 = 3300)
        from datetime import timedelta

        expected_expiry = datetime.now() + timedelta(seconds=3300)
        assert token_manager.token_expiry == expected_expiry

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_get_access_token_invalid_json_response(self, mock_post, token_manager):
        """Test handling of invalid JSON in response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        with pytest.raises(ValueError):
            token_manager.get_access_token()

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_get_access_token_missing_access_token_in_response(
        self, mock_post, token_manager
    ):
        """Test handling of response missing access_token field."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "token_type": "Bearer",
            "expires_in": 3600,
            # Missing 'access_token' field
        }
        mock_post.return_value = mock_response

        with pytest.raises(KeyError):
            token_manager.get_access_token()

    @pytest.mark.oauth
    @pytest.mark.unit
    @patch("email_campaign.requests.post")
    def test_multiple_token_requests(
        self, mock_post, token_manager, mock_successful_response
    ):
        """Test multiple token requests with proper caching."""
        from datetime import timedelta
        from freezegun import freeze_time

        mock_post.return_value = mock_successful_response

        with freeze_time("2024-01-01 12:00:00") as frozen_time:
            # First request should make HTTP call
            token1 = token_manager.get_access_token()
            assert token1 == "mock_access_token_12345"
            assert mock_post.call_count == 1

            # Second request should use cached token
            token2 = token_manager.get_access_token()
            assert token2 == "mock_access_token_12345"
            assert mock_post.call_count == 1  # No additional calls
            assert token1 == token2

            # Simulate time passing to expire token
            frozen_time.tick(delta=timedelta(hours=2))

            # Third request should make new HTTP call
            token3 = token_manager.get_access_token()
            assert mock_post.call_count == 2  # One additional call
            assert token3 == "mock_access_token_12345"
