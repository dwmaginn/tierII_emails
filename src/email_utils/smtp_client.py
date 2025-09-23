"""SMTP client for sending emails."""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SMTPClient:
    """SMTP client for sending emails through various providers."""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, use_tls: bool = True):
        """Initialize SMTP client.
        
        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password or app password
            use_tls: Whether to use TLS encryption
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    def send_email(self, to_addresses: List[str], subject: str, body: str, 
                   from_address: Optional[str] = None, cc_addresses: Optional[List[str]] = None,
                   bcc_addresses: Optional[List[str]] = None, html_body: Optional[str] = None) -> bool:
        """Send an email.
        
        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            body: Plain text email body
            from_address: Sender email address (defaults to username)
            cc_addresses: List of CC email addresses
            bcc_addresses: List of BCC email addresses
            html_body: HTML email body (optional)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_address or self.username
            msg['To'] = ', '.join(to_addresses)
            
            if cc_addresses:
                msg['Cc'] = ', '.join(cc_addresses)
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Combine all recipients
            all_recipients = to_addresses.copy()
            if cc_addresses:
                all_recipients.extend(cc_addresses)
            if bcc_addresses:
                all_recipients.extend(bcc_addresses)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                
                server.login(self.username, self.password)
                server.send_message(msg, to_addrs=all_recipients)
            
            logger.info(f"Email sent successfully to {len(all_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Test SMTP connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                
                server.login(self.username, self.password)
            
            logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False