"""Microsoft OAuth authentication manager implementation.

This module provides Microsoft OAuth 2.0 authentication management,
integrating with the existing OAuthTokenManager while conforming to
the BaseAuthenticationManager interface.
"""

from typing import Dict, Any, Optional
import logging
import base64
from datetime import datetime, timedelta

from .base_authentication_manager import (
    BaseAuthenticationManager,
    AuthenticationProvider,
    AuthenticationError,
    TokenExpiredError,
    InvalidCredentialsError,
    NetworkError,
)

# Import existing OAuthTokenManager
from .oauth_token_manager import OAuthTokenManager


class MicrosoftOAuthManager(BaseAuthenticationManager):
    """Microsoft OAuth 2.0 authentication manager.

    This class provides Microsoft OAuth authentication capabilities,
    integrating with the existing OAuthTokenManager implementation
    while conforming to the BaseAuthenticationManager interface.
    """

    def __init__(
        self, provider: AuthenticationProvider = AuthenticationProvider.MICROSOFT_OAUTH
    ):
        """Initialize Microsoft OAuth manager.

        Args:
            provider: Authentication provider (should be MICROSOFT_OAUTH)
        """
        super().__init__(provider)
        self._oauth_manager: Optional[OAuthTokenManager] = None
        self._logger = logging.getLogger(__name__)
        self._current_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def authenticate(self) -> bool:
        """Authenticate using Microsoft OAuth credentials.

        Uses the configuration set during initialization via set_configuration().

        Returns:
            True if authentication successful, False otherwise

        Raises:
            InvalidCredentialsError: If credentials are invalid
            NetworkError: If network request fails
            AuthenticationError: If authentication fails for other reasons
        """
        try:
            # Use configuration set during initialization
            config = self._config

            if not self.validate_configuration():
                raise InvalidCredentialsError(
                    "Invalid Microsoft OAuth configuration", self.provider
                )

            # Initialize OAuth manager if not already done
            if not self._oauth_manager and OAuthTokenManager:
                self._oauth_manager = OAuthTokenManager(
                    tenant_id=config["tenant_id"],
                    client_id=config["client_id"],
                    client_secret=config["client_secret"],
                )

            # Test authentication by getting a token
            token = self.get_access_token()
            if token:
                self.is_authenticated = True
                self.last_authentication_time = datetime.now()
                self._logger.info("Microsoft OAuth authentication successful")
                return True

            return False

        except InvalidCredentialsError:
            self.is_authenticated = False
            raise  # Re-raise InvalidCredentialsError as-is
        except Exception as e:
            self.is_authenticated = False

            if "invalid_client" in str(e).lower() or "unauthorized" in str(e).lower():
                raise InvalidCredentialsError(
                    f"Invalid OAuth credentials: {e}", self.provider
                )
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                raise NetworkError(
                    f"Network error during authentication: {e}", self.provider
                )
            else:
                raise AuthenticationError(f"Authentication failed: {e}", self.provider)

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Get valid access token for Microsoft OAuth.

        Args:
            force_refresh: Whether to force token refresh

        Returns:
            Valid access token

        Raises:
            AuthenticationError: If token acquisition fails
            TokenExpiredError: If token is expired and refresh fails
        """
        try:
            # Check if we have a valid cached token
            if not force_refresh and self._is_token_valid_cached():
                return self._current_token

            # Check if OAuth manager is available (must be initialized via authenticate)
            if not self._oauth_manager:
                raise AuthenticationError(
                    "OAuthTokenManager not available", self.provider
                )

            # Get token from OAuth manager
            token = self._oauth_manager.get_access_token()
            if not token:
                raise AuthenticationError(
                    "Failed to acquire access token", self.provider
                )

            # Cache the token with expiry
            self._current_token = token
            # Microsoft tokens typically expire in 1 hour, cache for 50 minutes
            self._token_expiry = datetime.now() + timedelta(minutes=50)

            return token

        except Exception as e:
            if "expired" in str(e).lower():
                raise TokenExpiredError(f"Token expired: {e}", self.provider)
            else:
                raise AuthenticationError(
                    f"Token acquisition failed: {e}", self.provider
                )

    def is_token_valid(self, token: Optional[str] = None) -> bool:
        """Check if the provided token is valid.

        Args:
            token: Token to validate (uses current token if None)

        Returns:
            True if token is valid, False otherwise
        """
        if token is None:
            return self._is_token_valid_cached()

        # For external tokens, we can't easily validate without making a request
        # This would require calling Microsoft's token validation endpoint
        # For now, return True if token exists and looks valid
        return bool(token and len(token) > 50)  # Basic length check

    def refresh_token(self) -> str:
        """Refresh the current access token.

        Returns:
            New access token

        Raises:
            TokenExpiredError: If refresh fails
            AuthenticationError: If refresh operation fails
        """
        if not self._oauth_manager:
            raise AuthenticationError("OAuthTokenManager not available", self.provider)

        try:
            # Force refresh by clearing cached token
            self._current_token = None
            self._token_expiry = None

            # Get new token
            return self.get_access_token(force_refresh=True)

        except Exception as e:
            raise TokenExpiredError(f"Failed to refresh token: {e}", self.provider)

    def get_smtp_auth_string(self, username: str, token: Optional[str] = None) -> str:
        """Generate SMTP authentication string for Microsoft OAuth.

        Args:
            username: Email address/username
            token: Access token (uses current token if None)

        Returns:
            Base64-encoded SMTP authentication string

        Raises:
            AuthenticationError: If token is not available
        """
        if token is None:
            if not self._oauth_manager:
                raise AuthenticationError(
                    "OAuthTokenManager not available", self.provider
                )
            token = self.get_access_token()

        if not token:
            raise AuthenticationError(
                "No valid token available for SMTP authentication", self.provider
            )

        # Create OAuth string in format: user=username\x01auth=Bearer token\x01\x01
        auth_string = f"user={username}\x01auth=Bearer {token}\x01\x01"

        # Encode to base64
        return base64.b64encode(auth_string.encode("ascii")).decode("ascii")

    def validate_configuration(self) -> bool:
        """Validate Microsoft OAuth configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        required_keys = ["tenant_id", "client_id", "client_secret"]

        # Check required keys exist and are not empty
        for key in required_keys:
            if key not in self._config or not self._config[key]:
                self._logger.error(
                    f"Missing or empty required configuration key: {key}"
                )
                return False

        # Validate tenant_id format (should be UUID or domain)
        tenant_id = self._config["tenant_id"]
        if not (self._is_valid_uuid(tenant_id) or self._is_valid_domain(tenant_id)):
            self._logger.error(f"Invalid tenant_id format: {tenant_id}")
            return False

        # Validate client_id format (should be UUID)
        client_id = self._config["client_id"]
        if not self._is_valid_uuid(client_id):
            self._logger.error(f"Invalid client_id format: {client_id}")
            return False

        # Validate sender_email if provided
        if "sender_email" in self._config and self._config["sender_email"]:
            sender_email = self._config["sender_email"]
            # Check basic email format
            if "@" not in sender_email or "." not in sender_email.split("@")[1]:
                self._logger.error(f"Invalid sender_email format: {sender_email}")
                return False
            # Check if it's a Microsoft domain
            if not self._is_microsoft_domain(sender_email):
                self._logger.error(
                    f"sender_email must be from a Microsoft domain: {sender_email}"
                )
                return False

        return True

    def _is_token_valid_cached(self) -> bool:
        """Check if cached token is still valid.

        Returns:
            True if cached token is valid, False otherwise
        """
        if not self._current_token or not self._token_expiry:
            return False

        return datetime.now() < self._token_expiry

    def _is_valid_uuid(self, value: str) -> bool:
        """Check if string is a valid UUID format.

        Args:
            value: String to validate

        Returns:
            True if valid UUID format, False otherwise
        """
        if value is None or not isinstance(value, str):
            return False

        try:
            import uuid

            uuid.UUID(value)
            return True
        except (ValueError, AttributeError, TypeError):
            return False

    def _is_valid_domain(self, value: str) -> bool:
        """Check if string is a valid domain format.

        Args:
            value: String to validate

        Returns:
            True if valid domain format, False otherwise
        """
        import re

        domain_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$"
        return bool(re.match(domain_pattern, value))

    def _validate_uuid(self, value: str) -> bool:
        """Validate UUID format (alias for _is_valid_uuid for test compatibility).

        Args:
            value: String to validate

        Returns:
            True if valid UUID format, False otherwise
        """
        return self._is_valid_uuid(value)

    def _is_microsoft_domain(self, email: str) -> bool:
        """Check if email belongs to a Microsoft domain.

        Args:
            email: Email address to check

        Returns:
            True if Microsoft domain, False otherwise
        """
        if not email or "@" not in email:
            return False

        domain = email.split("@")[1].lower()
        microsoft_domains = {
            "outlook.com",
            "hotmail.com",
            "live.com",
            "msn.com",
            "office365.com",
            "microsoft.com",
            "aiautocoach.com",
            "honestpharmco.com"
        }

        # Check exact match first
        if domain in microsoft_domains:
            return True

        # Check for onmicrosoft.com subdomains
        return domain.endswith(".onmicrosoft.com")

    def logout(self) -> None:
        """Clear authentication state and invalidate tokens.

        Overrides base class to also clear OAuth-specific state.
        """
        super().logout()
        self._oauth_manager = None
        self._current_token = None
        self._token_expiry = None
