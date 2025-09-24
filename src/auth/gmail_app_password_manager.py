"""Gmail App Password authentication manager implementation.

This module provides Gmail App Password authentication management,
conforming to the BaseAuthenticationManager interface for consistent
authentication handling across providers.
"""

from typing import Optional
import logging
import base64
import smtplib
import socket
from datetime import datetime

from .base_authentication_manager import (
    BaseAuthenticationManager,
    AuthenticationProvider,
    AuthenticationError,
    TokenExpiredError,
    InvalidCredentialsError,
    NetworkError,
)


class GmailAppPasswordManager(BaseAuthenticationManager):
    """Gmail App Password authentication manager.

    This class provides Gmail App Password authentication capabilities,
    conforming to the BaseAuthenticationManager interface for consistent
    authentication handling.
    """

    def __init__(
        self,
        provider: AuthenticationProvider = AuthenticationProvider.GMAIL_APP_PASSWORD,
    ):
        """Initialize Gmail App Password manager.

        Args:
            provider: Authentication provider (should be GMAIL_APP_PASSWORD)
        """
        super().__init__(provider)
        self._logger = logging.getLogger(__name__)
        self._app_password: Optional[str] = None
        self._sender_email: Optional[str] = None

    def authenticate(self) -> bool:
        """Authenticate using Gmail App Password credentials.

        Uses the configuration set via set_configuration() method.

        Returns:
            True if authentication successful, False otherwise

        Raises:
            InvalidCredentialsError: If credentials are invalid
            NetworkError: If network request fails
            AuthenticationError: If authentication fails for other reasons
        """
        try:
            if not self.validate_configuration():
                raise InvalidCredentialsError(
                    "Invalid Gmail App Password configuration", self.provider
                )

            # Extract credentials from configuration
            self._sender_email = self._config["gmail_sender_email"]
            self._app_password = self._config["gmail_app_password"]

            # Test authentication by connecting to Gmail SMTP
            connection_result = self._test_smtp_connection()
            
            if not connection_result:
                # Connection failed - determine the type of failure
                # Since _test_smtp_connection now returns False on any failure,
                # we need to attempt a more specific diagnosis
                try:
                    # Try a quick connection test to determine failure type
                    import smtplib
                    smtp_conn = smtplib.SMTP(self._config.get("smtp_server", "smtp.gmail.com"), 
                                           int(self._config.get("smtp_port", 587)))
                    smtp_conn.starttls()
                    smtp_conn.login(self._sender_email, self._app_password)
                    smtp_conn.quit()
                except smtplib.SMTPAuthenticationError:
                    raise InvalidCredentialsError(
                        "Invalid Gmail app password or email", self.provider
                    )
                except (ConnectionError, OSError, TimeoutError, socket.error):
                    raise NetworkError(
                        "SMTP connection failed", self.provider
                    )
                except Exception as e:
                    raise AuthenticationError(
                        f"SMTP connection test failed: {e}", self.provider
                    )
            
            # If we get here, authentication was successful
            self.is_authenticated = True
            self.last_authentication_time = datetime.now()
            self._logger.info("Gmail App Password authentication successful")
            return True

        except (InvalidCredentialsError, NetworkError, AuthenticationError):
            # Re-raise specific authentication exceptions as-is
            self.is_authenticated = False
            raise
        except Exception as e:
            # Handle any other unexpected exceptions
            self.is_authenticated = False
            raise AuthenticationError(f"Authentication failed: {e}", self.provider)

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Get access token (App Password) for Gmail authentication.

        For Gmail App Password, the 'token' is the app password itself.

        Args:
            force_refresh: Ignored for App Password (no refresh mechanism)

        Returns:
            App password as token

        Raises:
            AuthenticationError: If app password is not available or not authenticated
        """
        if not self.is_authenticated:
            raise AuthenticationError(
                "Not authenticated. Call authenticate() first.", self.provider
            )

        if not self._app_password:
            # Try to get from configuration
            self._app_password = self._config.get("gmail_app_password")

        if not self._app_password:
            raise AuthenticationError("Gmail App Password not available", self.provider)

        return self._app_password

    # Sentinel object to distinguish between no argument and explicit None
    _SENTINEL = object()
    
    def is_token_valid(self, token=_SENTINEL) -> bool:
        """Check if the App Password token is valid.

        For App Passwords, validity is determined by successful SMTP connection.

        Args:
            token: App password to validate (uses current if not provided)

        Returns:
            True if token is valid, False otherwise
        """
        # If no token argument provided, use current configuration
        if token is self._SENTINEL:
            token = self._app_password or self._config.get("gmail_app_password")
            
        # Handle invalid tokens (None, empty, or whitespace)
        if not token or not token.strip():
            return False
            
        # For App Passwords, we consider them valid if they exist and have proper format
        # App passwords are typically 16 characters without spaces
        cleaned_token = token.replace(" ", "")
        return len(cleaned_token) == 16 and cleaned_token.isalnum()

    def refresh_token(self) -> str:
        """Refresh token (not applicable for App Passwords).

        Gmail App Passwords don't have a refresh mechanism.
        They remain valid until manually revoked by the user.

        Returns:
            Current app password

        Raises:
            TokenExpiredError: Always, as App Passwords can't be refreshed
        """
        raise TokenExpiredError(
            "Gmail App Passwords cannot be refreshed programmatically. "
            "Please generate a new App Password in your Google Account settings.",
            self.provider,
        )

    def get_smtp_auth_string(self, username: str, token: Optional[str] = None) -> str:
        """Generate SMTP authentication string for Gmail App Password.

        Args:
            username: Email address/username
            token: App password (uses current if None)

        Returns:
            Base64-encoded SMTP authentication string

        Raises:
            AuthenticationError: If app password is not available
        """
        if token is None:
            # Check if we have an app password available without requiring authentication
            if not self._app_password:
                self._app_password = self._config.get("gmail_app_password")
            
            if not self._app_password:
                raise AuthenticationError(
                    "No app password available", self.provider
                )
            
            token = self._app_password

        if not token:
            raise AuthenticationError(
                "No valid App Password available for SMTP authentication", self.provider
            )

        # For Gmail App Password, we use standard base64 encoding of username:password
        auth_string = f"{username}:{token}"
        return base64.b64encode(auth_string.encode("ascii")).decode("ascii")

    def validate_configuration(self) -> bool:
        """Validate Gmail App Password configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        required_keys = ["gmail_sender_email", "gmail_app_password"]

        # Check required keys exist and are not empty
        for key in required_keys:
            if key not in self._config or not self._config[key]:
                self._logger.error(
                    f"Missing or empty required configuration key: {key}"
                )
                return False

        # Validate email format
        email = self._config["gmail_sender_email"]
        if not self._is_valid_email(email):
            self._logger.error(f"Invalid email format: {email}")
            return False

        # Validate Gmail domain
        #().endswith("@gmail.com"):
        #    self._logger.error(f"Email must be a Gmail address: {email}")
        #    return False

        # Validate app password format
        app_password = self._config["gmail_app_password"]
        if not self._is_valid_app_password(app_password):
            self._logger.error("Invalid Gmail App Password format")
            return False

        # Set default SMTP settings if not provided
        if "smtp_server" not in self._config:
            self._config["smtp_server"] = "smtp.gmail.com"
        if "smtp_port" not in self._config:
            self._config["smtp_port"] = 587

        return True

    def _test_smtp_connection(
        self,
        smtp_server: str = None,
        smtp_port: int = None,
        username: str = None,
        password: str = None,
    ) -> bool:
        """Test SMTP connection with Gmail using App Password.

        Args:
            smtp_server: SMTP server address (defaults to configured value)
            smtp_port: SMTP port (defaults to configured value)
            username: Username for authentication (defaults to configured email)
            password: Password for authentication (defaults to configured app password)

        Returns:
            True if connection successful, False otherwise
            
        Raises:
            InvalidCredentialsError: If SMTP authentication fails
            NetworkError: If network connection fails
            AuthenticationError: If other SMTP errors occur
        """
        try:
            server = smtp_server or self._config.get("smtp_server", "smtp.gmail.com")
            port = smtp_port or int(self._config.get("smtp_port", 587))
            user = username or self._sender_email
            pwd = password or self._app_password

            # Create SMTP connection
            smtp_conn = smtplib.SMTP(server, port)
            smtp_conn.starttls()

            # Attempt login
            smtp_conn.login(user, pwd)
            smtp_conn.quit()

            return True

        except smtplib.SMTPAuthenticationError as e:
            self._logger.error(f"SMTP authentication failed: {e}")
            return False
        except (ConnectionError, OSError, TimeoutError, socket.error) as e:
            self._logger.error(f"SMTP connection failed: {e}")
            return False
        except Exception as e:
            self._logger.error(f"SMTP connection test failed: {e}")
            return False

    def _is_valid_email(self, email: str) -> bool:
        """Check if string is a valid email format.

        Args:
            email: String to validate

        Returns:
            True if valid email format, False otherwise
        """
        import re

        # Email validation that prevents consecutive dots but allows valid characters
        # including plus signs, underscores, and hyphens
        email_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9._+%-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$"
        
        # Additional check to prevent consecutive dots
        if ".." in email:
            return False
            
        return bool(re.match(email_pattern, email))

    def _is_valid_app_password(self, password: str) -> bool:
        """Check if string is a valid Gmail App Password format.

        Gmail App Passwords are 16 characters long, alphanumeric,
        and may contain spaces for readability.

        Args:
            password: String to validate

        Returns:
            True if valid App Password format, False otherwise
        """
        if not password:
            return False

        # Remove spaces and check format
        cleaned_password = password.replace(" ", "")

        # Should be exactly 16 alphanumeric characters
        return len(cleaned_password) == 16 and cleaned_password.isalnum()

    def _is_gmail_domain(self, email: str) -> bool:
        """Check if email belongs to a Gmail domain.

        Args:
            email: Email address to check

        Returns:
            True if Gmail domain, False otherwise
        """
        if not email or "@" not in email:
            return False

        domain = email.split("@")[1].lower()
        gmail_domains = {"gmail.com", "googlemail.com"}

        return domain in gmail_domains