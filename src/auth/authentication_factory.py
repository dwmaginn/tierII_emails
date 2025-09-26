"""Authentication manager factory for provider selection and instantiation.

This module provides a factory pattern implementation for creating authentication
managers based on configuration and provider availability. It handles automatic
provider detection and fallback mechanisms.
"""

from typing import Optional, Dict, Any, List
import logging
from .base_authentication_manager import (
    BaseAuthenticationManager,
    AuthenticationProvider,
    AuthenticationError,
)


class AuthenticationFactory:
    """Factory class for creating authentication manager instances.

    This factory handles provider selection, configuration validation,
    and instantiation of appropriate authentication managers based on
    available credentials and configuration.
    """

    def __init__(self, settings: Optional[Any] = None):
        """Initialize the authentication factory.
        
        Args:
            settings: Optional settings object for configuration
        """
        self._providers: Dict[AuthenticationProvider, type] = {}
        self._settings = settings
        self._logger = logging.getLogger(__name__)

    def register_provider(
        self, provider: AuthenticationProvider, manager_class: type
    ) -> None:
        """Register an authentication provider with its manager class.

        Args:
            provider: The authentication provider enum
            manager_class: The manager class that implements BaseAuthenticationManager

        Raises:
            ValueError: If manager_class doesn't inherit from BaseAuthenticationManager
        """
        if not issubclass(manager_class, BaseAuthenticationManager):
            raise ValueError(
                f"Manager class {manager_class.__name__} must inherit from BaseAuthenticationManager"
            )

        self._providers[provider] = manager_class
        self._logger.info(f"Registered authentication provider: {provider.value}")

    def get_available_providers(self) -> List[AuthenticationProvider]:
        """Get list of registered authentication providers.

        Returns:
            List of available authentication providers
        """
        return list(self._providers.keys())

    def create_manager(
        self,
        provider: Optional[AuthenticationProvider] = None,
        config: Optional[Dict[str, Any]] = None,
        auto_detect: bool = True,
    ) -> BaseAuthenticationManager:
        """Create authentication manager for specified provider.

        Args:
            provider: Authentication provider to use (optional for auto-detection)
            config: Configuration dictionary containing provider-specific settings
            auto_detect: Whether to auto-detect provider if not specified

        Returns:
            BaseAuthenticationManager: Configured authentication manager

        Raises:
            AuthenticationError: If provider creation fails or no provider found
        """
        if config is None:
            config = {}

        # Auto-detect provider if not specified
        if provider is None and auto_detect:
            provider = self._detect_provider(config)
            if not provider:
                raise AuthenticationError(
                    "No suitable authentication provider found - only MailerSend is supported",
                    AuthenticationProvider.MAILERSEND,  # Default for error reporting
                )

        if provider is None:
            raise AuthenticationError(
                "No suitable authentication provider found",
                AuthenticationProvider.MAILERSEND,  # Default for error reporting
            )

        # Check cache first to avoid redundant manager creation
        from .authentication_cache import authentication_cache
        cached_manager = authentication_cache.get_manager(provider, config)
        if cached_manager is not None:
            self._logger.debug(f"Retrieved cached authentication manager for provider: {provider.value}")
            return cached_manager

        # Create new manager if not cached
        if provider not in self._providers:
            raise ValueError(
                f"Provider {provider.value} is not registered"
            )

        try:
            manager_class = self._providers[provider]
            manager = manager_class(provider)
            manager.set_configuration(config)

            if not manager.validate_configuration():
                raise AuthenticationError(
                    f"Invalid configuration for provider {provider.value}", provider
                )

            # Authenticate the manager
            print(f"DEBUG: About to authenticate manager for provider {provider.value}")
            auth_result = manager.authenticate()
            print(f"DEBUG: Authentication result: {auth_result}")
            if auth_result:
                # Cache the authenticated manager
                print(f"DEBUG: About to cache manager for provider {provider.value}")
                authentication_cache.cache_manager(provider, config, manager)
                self._logger.info(
                    f"Created and cached authentication manager for provider: {provider.value}"
                )
            else:
                self._logger.warning(
                    f"Authentication failed for provider: {provider.value}"
                )

            return manager
            
        except Exception as e:
            self._logger.error(f"Failed to create manager for provider {provider.value}: {e}")
            raise AuthenticationError(
                f"Invalid configuration for provider {provider.value}", provider
            )

    def create_with_fallback(
        self,
        primary_provider: AuthenticationProvider,
        fallback_providers: List[AuthenticationProvider],
        config: Dict[str, Any],
    ) -> BaseAuthenticationManager:
        """Create authentication manager with fallback support.

        Attempts to create manager with primary provider first, then falls back
        to other providers if primary fails.

        Args:
            primary_provider: Primary authentication provider to try
            fallback_providers: List of fallback providers to try
            config: Configuration dictionary

        Returns:
            Successfully configured authentication manager

        Raises:
            AuthenticationError: If all providers fail
        """
        providers_to_try = [primary_provider] + fallback_providers
        last_error = None

        for provider in providers_to_try:
            try:
                manager = self.create_manager(provider, config, auto_detect=False)
                self._logger.info(
                    f"Successfully created manager with provider: {provider.value}"
                )
                return manager
            except (AuthenticationError, ValueError) as e:
                last_error = e
                self._logger.warning(
                    f"Failed to create manager with provider {provider.value}: {e}"
                )
                continue

        raise AuthenticationError(
            f"All authentication providers failed. Last error: {last_error}",
            primary_provider,
        )

    def _detect_provider(
        self, config: Dict[str, Any]
    ) -> Optional[AuthenticationProvider]:
        """Auto-detect authentication provider based on configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Detected provider or None if detection fails
        """
        # Check for MailerSend configuration
        mailersend_keys = ["mailersend_api_token"]
        if all(key in config for key in mailersend_keys):
            self._logger.debug("Detected MailerSend configuration")
            return AuthenticationProvider.MAILERSEND

        self._logger.warning("Could not auto-detect authentication provider - only MailerSend is supported")
        return None

    def validate_provider_config(
        self, provider: AuthenticationProvider, config: Dict[str, Any]
    ) -> bool:
        """Validate configuration for a specific provider.

        Args:
            provider: Authentication provider to validate
            config: Configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        if provider not in self._providers:
            return False

        try:
            manager_class = self._providers[provider]
            if provider == AuthenticationProvider.MAILERSEND:
                from types import SimpleNamespace
                settings = SimpleNamespace(**config)
                temp_manager = manager_class(settings)
            else:
                raise ValueError(f"Unsupported provider: {provider.value}")
            return temp_manager.validate_configuration()
        except Exception as e:
            self._logger.error(
                f"Configuration validation failed for {provider.value}: {e}"
            )
            return False


# Global factory instance
authentication_factory = AuthenticationFactory()
