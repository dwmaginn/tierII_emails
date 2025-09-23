"""Authentication module for email campaign system.

This module provides a unified authentication interface supporting multiple
providers including Microsoft OAuth and Gmail App Passwords. It implements
the factory pattern for provider selection and consistent error handling.

Usage:
    from auth import authentication_factory, AuthenticationProvider
    
    # Auto-detect provider
    manager = authentication_factory.create_manager(config=config)
    
    # Specify provider
    manager = authentication_factory.create_manager(
        provider=AuthenticationProvider.MICROSOFT_OAUTH,
        config=config
    )
    
    # Authenticate and get token
    if manager.authenticate(credentials):
        token = manager.get_access_token()
        auth_string = manager.get_smtp_auth_string(username, token)
"""

from .base_authentication_manager import (
    BaseAuthenticationManager,
    AuthenticationProvider,
    AuthenticationError,
    TokenExpiredError,
    InvalidCredentialsError,
    NetworkError,
)
from .authentication_factory import AuthenticationFactory, authentication_factory
from .oauth_token_manager import OAuthTokenManager
from .microsoft_oauth_manager import MicrosoftOAuthManager
from .gmail_app_password_manager import GmailAppPasswordManager

# Register providers with the global factory
authentication_factory.register_provider(
    AuthenticationProvider.MICROSOFT_OAUTH, MicrosoftOAuthManager
)

authentication_factory.register_provider(
    AuthenticationProvider.GMAIL_APP_PASSWORD, GmailAppPasswordManager
)

__all__ = [
    # Base classes and interfaces
    "BaseAuthenticationManager",
    "AuthenticationProvider",
    # Exception classes
    "AuthenticationError",
    "TokenExpiredError",
    "InvalidCredentialsError",
    "NetworkError",
    # Factory classes
    "AuthenticationFactory",
    "authentication_factory",
    # Provider implementations
    "OAuthTokenManager",
    "MicrosoftOAuthManager",
    "GmailAppPasswordManager",
]

# Version information
__version__ = "1.0.0"
__author__ = "Email Campaign System"
__description__ = "Unified authentication interface for email providers"
