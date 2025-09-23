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
        """Create an authentication manager instance.

        Args:
            provider: Specific provider to use (optional)
            config: Configuration dictionary (optional)
            auto_detect: Whether to auto-detect provider if not specified

        Returns:
            Configured authentication manager instance

        Raises:
            AuthenticationError: If no suitable provider found or configuration invalid
            ValueError: If specified provider is not registered
        """
        config = config or {}

        # If provider specified, use it directly
        if provider:
            if provider not in self._providers:
                raise ValueError(f"Provider {provider.value} is not registered")

            manager_class = self._providers[provider]
            manager = manager_class(provider)
            manager.set_configuration(config)

            if not manager.validate_configuration():
                raise AuthenticationError(
                    f"Invalid configuration for provider {provider.value}", provider
                )

            self._logger.info(
                f"Created authentication manager for provider: {provider.value}"
            )
            return manager

        # Auto-detect provider based on configuration
        if auto_detect:
            detected_provider = self._detect_provider(config)
            if detected_provider:
                return self.create_manager(detected_provider, config, auto_detect=False)

        raise AuthenticationError(
            "No suitable authentication provider found",
            AuthenticationProvider.MICROSOFT_OAUTH,  # Default for error reporting
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
        # Check for Microsoft OAuth configuration
        microsoft_keys = ["tenant_id", "client_id", "client_secret"]
        if all(key in config for key in microsoft_keys):
            self._logger.debug("Detected Microsoft OAuth configuration")
            return AuthenticationProvider.MICROSOFT_OAUTH

        # Check for Gmail App Password configuration
        gmail_keys = ["gmail_app_password", "gmail_sender_email"]
        if all(key in config for key in gmail_keys):
            self._logger.debug("Detected Gmail App Password configuration")
            return AuthenticationProvider.GMAIL_APP_PASSWORD

        # Check SMTP server-based detection
        smtp_server = config.get("smtp_server", "").lower()
        if (
            "outlook.office365.com" in smtp_server
            or "smtp.office365.com" in smtp_server
        ):
            self._logger.debug("Detected Microsoft SMTP server")
            return AuthenticationProvider.MICROSOFT_OAUTH
        elif "smtp.gmail.com" in smtp_server:
            self._logger.debug("Detected Gmail SMTP server")
            return AuthenticationProvider.GMAIL_APP_PASSWORD

        self._logger.warning("Could not auto-detect authentication provider")
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
            temp_manager = manager_class(provider)
            temp_manager.set_configuration(config)
            return temp_manager.validate_configuration()
        except Exception as e:
            self._logger.error(
                f"Configuration validation failed for {provider.value}: {e}"
            )
            return False


# Global factory instance
authentication_factory = AuthenticationFactory()
