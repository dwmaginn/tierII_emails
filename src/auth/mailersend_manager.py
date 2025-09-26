"""MailerSend authentication manager implementation.

This module provides MailerSend API integration for the tierII_emails system,
implementing the BaseAuthenticationManager interface for consistent behavior
with other authentication providers.
"""

import re
import logging
import urllib3
from typing import Optional, Dict, Any, ClassVar
from datetime import datetime
import threading

from mailersend import MailerSendClient, EmailBuilder
from mailersend.exceptions import MailerSendError, AuthenticationError as MailerSendAuthError

from .base_authentication_manager import (
    BaseAuthenticationManager,
    AuthenticationProvider,
    AuthenticationError,
    InvalidCredentialsError,
    NetworkError,
)


class MailerSendManager(BaseAuthenticationManager):
    """MailerSend authentication and email sending manager.
    
    This class handles authentication with MailerSend API and provides
    email sending functionality using the MailerSend service.
    Implements singleton pattern for client instances to minimize API calls.
    """

    # Class-level client cache for singleton pattern
    _client_cache: ClassVar[Dict[str, MailerSendClient]] = {}
    _cache_lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, provider: AuthenticationProvider):
        """Initialize MailerSend manager with provider type.
        
        Args:
            provider: The authentication provider type
            
        Note:
            Configuration must be set using set_configuration() after initialization.
        """
        # Initialize base class with provider type
        super().__init__(provider)
        
        self._logger = logging.getLogger(__name__)
        
        # Initialize last_authenticated attribute
        self.last_authenticated = None
        
        # Client will be initialized lazily
        self._client = None
        self._api_key = None
        self.settings = None

    def _get_client_cache_key(self) -> str:
        """Generate cache key for client singleton pattern.
        
        Returns:
            str: Cache key based on API key hash
        """
        if not self._api_key:
            return ""
        # Use first 16 chars of API key as cache key for security
        return f"mailersend_{self._api_key[:16]}"

    def _initialize_client(self) -> None:
        """Initialize the MailerSend client using singleton pattern."""
        if not self._api_key:
            raise InvalidCredentialsError(
                "API key not configured",
                AuthenticationProvider.MAILERSEND,
                "NO_API_KEY"
            )
            
        cache_key = self._get_client_cache_key()
        
        # Check if client already exists in cache
        with self._cache_lock:
            if cache_key in self._client_cache:
                self._client = self._client_cache[cache_key]
                self._logger.debug(f"Reusing cached MailerSend client for key: {cache_key[:8]}...")
                return
        
        try:
            # Create new client
            client = MailerSendClient(api_key=self._api_key)
            
            # Disable urllib3 automatic retries to prevent interference with our retry logic
            if hasattr(client, 'session') and client.session:
                session = client.session
                for adapter in session.adapters.values():
                    if hasattr(adapter, 'max_retries'):
                        # Disable all automatic retries
                        adapter.max_retries = urllib3.util.Retry(
                            total=0,
                            read=False,
                            connect=False,
                            backoff_factor=0
                        )
                        adapter.max_retries.respect_retry_after_header = False
            
            # Cache the client and assign to instance
            with self._cache_lock:
                self._client_cache[cache_key] = client
                self._client = client
            
            self._logger.debug(f"MailerSend client initialized and cached successfully for key: {cache_key[:8]}...")
        except Exception as e:
            self._logger.error(f"Failed to initialize MailerSend client: {e}")
            raise InvalidCredentialsError(
                f"Failed to initialize MailerSend client: {e}",
                AuthenticationProvider.MAILERSEND,
                "CLIENT_INIT_ERROR"
            )

    def get_access_token(self) -> str:
        """Get a valid access token for MailerSend API authentication.
        
        For MailerSend, this returns the API key as it's used for authentication.
        
        Returns:
            Valid API key string
            
        Raises:
            AuthenticationError: If not authenticated or API key unavailable
        """
        if not self.is_authenticated:
            raise AuthenticationError(
                "Not authenticated with MailerSend",
                AuthenticationProvider.MAILERSEND,
                "NOT_AUTHENTICATED"
            )
        
        return self._api_key

    def is_token_valid(self) -> bool:
        """Check if the current authentication token is valid.
        
        For MailerSend, we check if we have an API key and are authenticated.
        
        Returns:
            True if token is valid and not expired, False otherwise
        """
        return bool(self._api_key and self.is_authenticated)

    def refresh_token(self) -> bool:
        """Refresh the authentication token if supported by provider.
        
        MailerSend uses API keys which don't expire, so this always returns True
        if we have a valid API key.
        
        Returns:
            True if token refresh successful, False otherwise
        """
        return self.is_token_valid()

    def _validate_mailersend_api_key_format(self, api_key: str) -> bool:
        """Validate MailerSend API key format without making API calls.
        
        MailerSend API keys follow the pattern: super-secret-mailersend-token followed by optional characters
        
        Args:
            api_key: The API key to validate
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # MailerSend API key pattern: super-secret-mailersend-token + optional characters
        pattern = r'^super-secret-mailersend.*'
        return bool(re.match(pattern, api_key))



    def validate_configuration(self) -> bool:
        """Validate MailerSend configuration settings.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            # Check if configuration has been set
            config = self.get_configuration()
            
            # Check required API token
            api_token = config.get('mailersend_api_token')
            if not api_token or not api_token.strip():
                self._logger.error("MailerSend API token is required")
                return False
            
            # Validate API key format
            if not self._validate_mailersend_api_key_format(api_token.strip()):
                self._logger.error("Invalid MailerSend API key format. Expected format: super-secret-mailersend-token followed by optional characters")
                return False
            
            # Check required sender email
            sender_email = config.get('sender_email')
            if not sender_email or not sender_email.strip():
                self._logger.error("Sender email is required for MailerSend")
                return False
            
            # Validate email format
            if not self._is_valid_email(sender_email):
                self._logger.error(f"Invalid sender email format: {sender_email}")
                return False
            
            # Store API key for later initialization
            self._api_key = api_token.strip()
            
            # Create settings object for backward compatibility
            from types import SimpleNamespace
            self.settings = SimpleNamespace(**config)
            
            # Initialize client after successful validation
            self._initialize_client()
            
            return True
            
        except Exception as e:
            self._logger.error(f"Configuration validation failed: {e}")
            return False

    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email format is valid
        """
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def authenticate(self) -> bool:
        """Authenticate with MailerSend API using format validation only.
        
        This method validates the API key format without making API calls
        to prevent rate limiting issues. Actual API validation is deferred
        to the first email send attempt.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            InvalidCredentialsError: If API key format is invalid
            NetworkError: If unexpected error occurs during validation
        """
        try:
            self._logger.debug("Authenticating with MailerSend API (format validation only)")
            
            # Validate API key format without making API calls
            if not self._validate_mailersend_api_key_format(self._api_key):
                raise InvalidCredentialsError(
                    "Invalid MailerSend API key format. Expected format: super-secret-mailersend-token followed by optional characters",
                    AuthenticationProvider.MAILERSEND,
                    "INVALID_API_KEY_FORMAT"
                )
            
            # Set authentication status based on format validation
            self.is_authenticated = True
            self.last_authenticated = datetime.now()
            self._logger.info("MailerSend authentication successful (format validated)")
            return True
                
        except InvalidCredentialsError:
            raise
        except Exception as e:
            self._logger.error(f"Network error during MailerSend authentication: {e}")
            raise NetworkError(
                f"Network error during MailerSend authentication: {e}",
                AuthenticationProvider.MAILERSEND,
                "NETWORK_ERROR"
            )

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email using MailerSend API.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            AuthenticationError: If not authenticated
            ValueError: If required parameters are missing
        """
        # Validate authentication
        if not self.is_authenticated:
            raise AuthenticationError(
                "Not authenticated with MailerSend",
                AuthenticationProvider.MAILERSEND,
                "NOT_AUTHENTICATED"
            )
        
        # Validate required parameters
        if not to_email or not to_email.strip():
            raise ValueError("Recipient email is required")
        
        if not subject or not subject.strip():
            raise ValueError("Email subject is required")
        
        if not html_content or not html_content.strip():
            raise ValueError("Email content is required")
        
        # Generate text content if not provided
        if not text_content:
            text_content = self._html_to_text(html_content)
        
        return self._send_via_mailersend(
            to_email=to_email.strip(),
            to_name=to_name or "",
            subject=subject.strip(),
            html_content=html_content,
            text_content=text_content
        )

    def _send_via_mailersend(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """Internal method to send email via MailerSend API.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            AuthenticationError: If sending fails due to API errors
        """
        try:
            # Initialize client if not already done (uses singleton pattern)
            if self._client is None:
                self._initialize_client()
            
            # Build email using MailerSend EmailBuilder
            email = (EmailBuilder()
                    .from_email(
                        self.settings.sender_email,
                        getattr(self.settings, 'sender_name', 'TierII System')
                    )
                    .to_many([{"email": to_email, "name": to_name}])
                    .subject(subject)
                    .html(html_content)
                    .text(text_content)
                    .build())
            
            # Send email
            response = self._client.emails.send(email)
            
            if response.status_code == 202:  # MailerSend returns 202 for accepted
                self._logger.info(f"Email sent successfully to {to_email}")
                return True
            elif response.status_code == 429:  # Rate limit exceeded
                error_msg = f"Rate limit exceeded (429): Too many requests"
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg += f" - {error_data['message']}"
                except:
                    pass
                self._logger.error(error_msg)
                raise AuthenticationError(error_msg, self.provider, "RATE_LIMIT")
            else:
                error_msg = f"Email sending failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg += f": {error_data['message']}"
                except:
                    pass
                self._logger.error(error_msg)
                raise AuthenticationError(error_msg, self.provider, "SEND_FAILED")
                
        except MailerSendError as e:
            error_msg = f"MailerSend API error: {str(e)}"
            self._logger.error(error_msg)
            raise AuthenticationError(error_msg, self.provider, "API_ERROR")
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            self._logger.error(error_msg)
            raise AuthenticationError(error_msg, self.provider, "UNKNOWN_ERROR")

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text.
        
        Args:
            html_content: HTML content to convert
            
        Returns:
            str: Plain text version of the content
        """
        if not html_content:
            return ""
        
        try:
            # Simple HTML to text conversion
            # Remove HTML tags
            import re
            text = re.sub(r'<[^>]+>', '', html_content)
            
            # Decode HTML entities
            text = text.replace('&amp;', '&')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            text = text.replace('&quot;', '"')
            text = text.replace('&#39;', "'")
            text = text.replace('&nbsp;', ' ')
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text
            
        except Exception as e:
            self._logger.warning(f"Error converting HTML to text: {e}")
            return html_content  # Return original if conversion fails

    def get_provider_name(self) -> str:
        """Get human-readable provider name.
        
        Returns:
            str: Provider name
        """
        return "MailerSend"

    def get_authentication_status(self) -> Dict[str, Any]:
        """Get current authentication status information.
        
        Returns:
            Dict containing authentication status details
        """
        return {
            "authenticated": self.is_authenticated,
            "provider": self.get_provider_name(),
            "last_authenticated": self.last_authenticated,
            "api_key_configured": bool(self._api_key),
        }

    @classmethod
    def clear_client_cache(cls) -> None:
        """Clear the client cache. Useful for testing or memory management.
        
        This method should be used sparingly in production as it will force
        re-initialization of clients on next use.
        """
        with cls._cache_lock:
            cls._client_cache.clear()
            
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Get statistics about the client cache.
        
        Returns:
            Dict containing cache statistics
        """
        with cls._cache_lock:
            return {
                "cached_clients": len(cls._client_cache),
                "cache_keys": list(cls._client_cache.keys())
            }