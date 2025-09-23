"""OAuth Token Manager for Microsoft 365 authentication.

This module provides OAuth 2.0 token management functionality
for Microsoft 365 services, extracted from the main email_campaign module
to avoid configuration dependencies during testing.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Optional


class OAuthTokenManager:
    """Manages OAuth 2.0 tokens for Microsoft 365 authentication."""

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """Initialize the OAuth token manager.

        Args:
            tenant_id: Microsoft 365 tenant ID
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
        self.scope = "https://outlook.office365.com/.default"

    def get_access_token(self, force_refresh: bool = False) -> Optional[str]:
        """Get a valid access token, refreshing if necessary.

        Args:
            force_refresh: Force token refresh even if current token is valid

        Returns:
            Valid access token or None if authentication fails
        """
        # Check if we have a valid token and don't need to refresh
        if not force_refresh and self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry - timedelta(minutes=5):
                return self.access_token

        # Need to get a new token
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            print(
                "Error: Missing OAuth credentials (tenant_id, client_id, client_secret)"
            )
            return None

        token_url = (
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        )

        token_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
        }

        try:
            response = requests.post(token_url, data=token_data, timeout=30)
            response.raise_for_status()

            token_info = response.json()
            self.access_token = token_info["access_token"]
            expires_in = token_info.get("expires_in", 3600)  # Default to 1 hour
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            print(
                f"Successfully obtained access token. Expires at: {self.token_expiry}"
            )
            return self.access_token

        except requests.exceptions.RequestException as e:
            print(f"Error obtaining access token: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing token response: {e}")
            return None
        except KeyError as e:
            print(f"Missing key in token response: {e}")
            return None

    def is_token_valid(self) -> bool:
        """Check if the current token is valid.

        Returns:
            True if token is valid, False otherwise
        """
        if not self.access_token or not self.token_expiry:
            return False

        # Consider token invalid if it expires within 5 minutes
        return datetime.now() < self.token_expiry - timedelta(minutes=5)

    def clear_token(self) -> None:
        """Clear the stored token."""
        self.access_token = None
        self.token_expiry = None
