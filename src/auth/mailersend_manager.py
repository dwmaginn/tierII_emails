"""MailerSend authentication manager implementation.

This module provides MailerSend API integration for the tierII_emails system,
implementing the BaseAuthenticationManager interface for consistent behavior
with other authentication providers.
"""

import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime

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
    """

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
        
        # These will be set when configuration is provided
        self._api_key = None
        self._client = None
        self.settings = None

    def _initialize_client(self) -> None:
        """Initialize the MailerSend client."""
        try:
            self._client = MailerSendClient(api_key=self._api_key)
            self._logger.debug("MailerSend client initialized successfully")
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
            
            # Check required sender email
            sender_email = config.get('sender_email')
            if not sender_email or not sender_email.strip():
                self._logger.error("Sender email is required for MailerSend")
                return False
            
            # Validate email format
            if not self._is_valid_email(sender_email):
                self._logger.error(f"Invalid sender email format: {sender_email}")
                return False
            
            # Initialize API key and client if validation passes
            self._api_key = api_token.strip()
            self._initialize_client()
            
            # Create settings object for backward compatibility
            from types import SimpleNamespace
            self.settings = SimpleNamespace(**config)
            
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
        """Authenticate with MailerSend API.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            InvalidCredentialsError: If API key is invalid
            NetworkError: If network error occurs during authentication
        """
        try:
            self._logger.debug("Authenticating with MailerSend API")
            
            # Test authentication by making a simple API call
            # Use a minimal request to check API key validity
            from mailersend.models import TokensListRequest
            request = TokensListRequest()
            response = self._client.tokens.list_tokens(request)
            
            if response.status_code == 200:
                self.is_authenticated = True
                self.last_authenticated = datetime.now()
                self._logger.info("MailerSend authentication successful")
                return True
            elif response.status_code == 401:
                raise InvalidCredentialsError(
                    "Invalid MailerSend API key",
                    AuthenticationProvider.MAILERSEND,
                    "INVALID_API_KEY"
                )
            else:
                raise AuthenticationError(
                    f"MailerSend authentication failed with status {response.status_code}",
                    AuthenticationProvider.MAILERSEND,
                    f"HTTP_{response.status_code}"
                )
                
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
            else:
                error_msg = f"Failed to send email: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg += f" - {error_data['message']}"
                except:
                    pass
                
                raise AuthenticationError(
                    error_msg,
                    AuthenticationProvider.MAILERSEND,
                    f"SEND_ERROR_{response.status_code}"
                )
                
        except AuthenticationError:
            raise
        except Exception as e:
            self._logger.error(f"Error sending email via MailerSend: {e}")
            raise AuthenticationError(
                f"Error sending email via MailerSend: {e}",
                AuthenticationProvider.MAILERSEND,
                "SEND_ERROR"
            )

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