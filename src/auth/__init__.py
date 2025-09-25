"""Authentication module for email campaign system.

This module provides a unified authentication interface for MailerSend API.
It implements the factory pattern for provider selection and consistent error handling.

Usage:
    from auth import authentication_factory, AuthenticationProvider
    
    # Auto-detect provider
    manager = authentication_factory.create_manager(config=config)
    
    # Specify provider
    manager = authentication_factory.create_manager(
        provider=AuthenticationProvider.MAILERSEND,
        config=config
    )
    
    # Authenticate and get API key
    if manager.authenticate(credentials):
        api_key = manager.get_access_token()
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
from .mailersend_manager import MailerSendManager

# Register providers with the global factory
authentication_factory.register_provider(
    AuthenticationProvider.MAILERSEND, MailerSendManager
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
    "MailerSendManager",
]

# Version information
__version__ = "0.1.0"
__author__ = "Email Campaign System"
__description__ = "Unified authentication interface for email providers"
