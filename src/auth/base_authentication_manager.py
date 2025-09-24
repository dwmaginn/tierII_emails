"""Base authentication manager abstract class.

Defines the common interface for all authentication providers in the tierII_emails system.
This abstract class ensures consistent authentication behavior across MailerSend API
and any future authentication providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AuthenticationProvider(Enum):
    """Enumeration of supported authentication providers."""

    MAILERSEND = "mailersend"


class AuthenticationError(Exception):
    """Base exception for authentication-related errors."""

    def __init__(
        self,
        message: str,
        provider: AuthenticationProvider,
        error_code: Optional[str] = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.timestamp = datetime.now()


class TokenExpiredError(AuthenticationError):
    """Exception raised when authentication token has expired."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Exception raised when provided credentials are invalid."""

    pass


class NetworkError(AuthenticationError):
    """Exception raised when network-related authentication failures occur."""

    pass


class BaseAuthenticationManager(ABC):
    """Abstract base class for authentication managers.

    This class defines the common interface that all authentication providers
    must implement. It ensures consistent behavior across different authentication
    methods while allowing provider-specific implementations.

    Attributes:
        provider: The authentication provider type
        is_authenticated: Whether the manager is currently authenticated
        last_authentication_time: Timestamp of last successful authentication
    """

    def __init__(self, provider: AuthenticationProvider):
        """Initialize the authentication manager.

        Args:
            provider: The authentication provider type
        """
        self.provider = provider
        self.is_authenticated = False
        self.last_authentication_time: Optional[datetime] = None
        self._config: Dict[str, Any] = {}

    @abstractmethod
    def authenticate(self) -> bool:
        """Perform authentication with the provider.

        Returns:
            True if authentication successful, False otherwise

        Raises:
            AuthenticationError: If authentication fails due to provider-specific issues
            InvalidCredentialsError: If credentials are invalid
            NetworkError: If network-related issues prevent authentication
        """
        pass

    @abstractmethod
    def get_access_token(self) -> str:
        """Get a valid access token for API authentication.

        This method should handle token refresh automatically if the current
        token is expired or about to expire.

        Returns:
            Valid access token string

        Raises:
            AuthenticationError: If unable to obtain or refresh token
            TokenExpiredError: If token is expired and cannot be refreshed
        """
        pass

    @abstractmethod
    def is_token_valid(self) -> bool:
        """Check if the current authentication token is valid.

        Returns:
            True if token is valid and not expired, False otherwise
        """
        pass

    @abstractmethod
    def refresh_token(self) -> bool:
        """Refresh the authentication token if supported by provider.

        Returns:
            True if token refresh successful, False otherwise

        Raises:
            AuthenticationError: If token refresh fails
        """
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate that all required configuration is present and valid.

        Returns:
            True if configuration is valid, False otherwise

        Raises:
            AuthenticationError: If configuration validation fails
        """
        pass

    def get_provider_name(self) -> str:
        """Get the human-readable name of the authentication provider.

        Returns:
            Provider name string
        """
        return self.provider.value.replace("_", " ").title()

    def get_authentication_status(self) -> Dict[str, Any]:
        """Get current authentication status information.

        Returns:
            Dictionary containing authentication status details
        """
        return {
            "provider": self.provider.value,
            "is_authenticated": self.is_authenticated,
            "last_authentication_time": self.last_authentication_time,
            "token_valid": self.is_token_valid() if self.is_authenticated else False,
        }

    def logout(self) -> None:
        """Clear authentication state and invalidate tokens.

        This method should be called when logging out or switching providers.
        """
        self.is_authenticated = False
        self.last_authentication_time = None

    def set_configuration(self, config: Dict[str, Any]) -> None:
        """Set provider-specific configuration.

        Args:
            config: Dictionary containing provider-specific configuration
        """
        self._config.update(config)

    def get_configuration(self) -> Dict[str, Any]:
        """Get current provider configuration.

        Returns:
            Dictionary containing current configuration
        """
        return self._config.copy()
