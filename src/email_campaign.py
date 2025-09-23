import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import sys
import base64
from datetime import datetime, timedelta
from typing import Optional
import logging
import os

# Import authentication components
from auth.authentication_factory import authentication_factory
from auth.base_authentication_manager import (
    AuthenticationError,
    TokenExpiredError,
    InvalidCredentialsError,
    NetworkError,
    AuthenticationProvider
)

# Import configuration from new settings module
# Legacy config.py has been replaced with config/settings.py

# Import settings for authentication configuration
try:
    from config.settings import TierIISettings
    settings = TierIISettings()
except ImportError:
    print(
        "Warning: settings.py not found. Using legacy configuration."
    )
    settings = None

# Legacy configuration fallback
TENANT_ID = os.getenv('TENANT_ID')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.office365.com')
SMTP_PORT = os.getenv('SMTP_PORT', '587')

# Campaign configuration
if settings:
    BATCH_SIZE = settings.campaign_batch_size
    DELAY_MINUTES = settings.campaign_delay_minutes
else:
    BATCH_SIZE = int(os.getenv('TIERII_CAMPAIGN_BATCH_SIZE', '10'))
    DELAY_MINUTES = int(os.getenv('TIERII_CAMPAIGN_DELAY_MINUTES', '5'))

# Email template
SUBJECT = "High-Quality Cannabis Available - Honest Pharmco"


class EmailCampaign:
    """Email campaign management class."""
    
    def __init__(self, csv_file=None, batch_size=10, delay_minutes=5):
        self.csv_file = csv_file or "tier_i_tier_ii_emails_verified.csv"
        self.batch_size = batch_size
        self.delay_minutes = delay_minutes
        self.contacts = []
        
    def load_contacts(self):
        """Load contacts from CSV file."""
        self.contacts = read_contacts_from_csv(self.csv_file)
        return self.contacts
        
    def send_campaign(self):
        """Send the email campaign."""
        if not self.contacts:
            self.load_contacts()
        
        if not self.contacts:
            print("No contacts found. Exiting.")
            return False
            
        total_sent = 0
        start_index = 0
        
        while start_index < len(self.contacts):
            successful_sends, next_index = send_batch_emails(
                self.contacts, start_index, self.batch_size
            )
            total_sent += successful_sends
            start_index = next_index
            
            # If there are more batches to send, wait for the specified delay
            if start_index < len(self.contacts):
                time.sleep(self.delay_minutes * 60)
                
        return total_sent


# Initialize authentication manager with fallback
def create_authentication_manager():
    """Create authentication manager with Microsoft OAuth -> Gmail fallback."""
    try:
        # Use settings if available, otherwise fall back to legacy config
        if settings:
            # Configure from settings
            config = {
                "tenant_id": getattr(settings, 'microsoft_tenant_id', None),
                "client_id": getattr(settings, 'microsoft_client_id', None),
                "client_secret": getattr(settings, 'microsoft_client_secret', None),
                "sender_email": getattr(settings, 'sender_email', None),
                "smtp_server": getattr(settings, 'smtp_server', None),
                "smtp_port": getattr(settings, 'smtp_port', None),
                "gmail_sender_email": getattr(settings, 'gmail_sender_email', None),
                "gmail_app_password": getattr(settings, 'gmail_app_password', None)
            }
            
            return authentication_factory.create_with_fallback(
                primary_provider=AuthenticationProvider.MICROSOFT_OAUTH,
                fallback_providers=[AuthenticationProvider.GMAIL_APP_PASSWORD],
                config=config
            )
        else:
            # Legacy configuration fallback
            # Configure Microsoft OAuth from legacy config
            microsoft_config = {
                "tenant_id": TENANT_ID,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "sender_email": SENDER_EMAIL,
                "smtp_server": SMTP_SERVER,
                "smtp_port": SMTP_PORT
            }
            
            return authentication_factory.create_with_fallback(
                primary_provider=AuthenticationProvider.MICROSOFT_OAUTH,
                fallback_providers=[AuthenticationProvider.GMAIL_APP_PASSWORD],
                config=microsoft_config
            )
    except Exception as e:
        print(f"✗ Failed to initialize authentication manager: {e}")
        raise

# Global authentication manager instance
try:
    auth_manager = create_authentication_manager()
    print(f"✓ Authentication manager initialized with provider: {auth_manager.get_current_manager().provider.name}")
except Exception as e:
    print(f"Failed to initialize authentication manager: {e}")
    auth_manager = None


def get_oauth_string(username, access_token):
    """Generate OAuth string for SMTP authentication"""
    auth_string = f"user={username}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_string.encode()).decode()


def get_first_name(contact_name):
    """Extract first name from contact name"""
    if not contact_name:
        return "there"

    # Split by common delimiters and take first part
    name_parts = contact_name.split()
    if name_parts:
        first_name = name_parts[0].strip()
        # Remove common titles (with and without periods)
        titles = [
            "mr",
            "mrs",
            "ms",
            "dr",
            "prof",
            "rev",
            "sir",
            "madam",
            "mr.",
            "mrs.",
            "ms.",
            "dr.",
            "prof.",
            "rev.",
            "sir.",
            "madam.",
        ]
        first_name_lower = first_name.lower()
        if first_name_lower in titles:
            return name_parts[1].strip() if len(name_parts) > 1 else "there"
        return first_name

    return "there"


def send_email(recipient_email, first_name, max_retries=3):
    """Send email to a single recipient using authentication manager with fallback.
    
    Args:
        recipient_email: Email address to send to
        first_name: Personalized first name for email
        max_retries: Maximum number of retry attempts
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    for attempt in range(max_retries):
        try:
            # Create message
            msg = MIMEMultipart()
            sender_email = settings.sender_email if settings else "default@example.com"
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = SUBJECT

            # Email body with personalized first name
            body = f"""Hi {first_name},

This is David from Honest Pharmco. We have a variety of high-quality cannabis available in sativa, indica, and hybrid strains, all with high THC percentages, including:
B&C's
Smalls
Premium flower

Our pricing starts at $600/lb for our lowest grade and increases from there based on quality.

Please feel free to reach out with any questions or to discuss availability.

Best,
David"""

            msg.attach(MIMEText(body, "plain"))

            # Authenticate and send email
            success = _send_with_authentication(msg, recipient_email)
            
            if success:
                print(f"✓ Email sent successfully to {recipient_email}")
                return True
            else:
                # If authentication failed, try fallback on next attempt
                if attempt < max_retries - 1:
                    print(f"⚠ Attempt {attempt + 1} failed, retrying with fallback...")
                    time.sleep(2)  # Brief delay before retry
                    continue
                    
        except (AuthenticationError, TokenExpiredError, InvalidCredentialsError) as e:
            print(f"✗ Authentication error for {recipient_email} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print(f"⚠ Retrying with fallback authentication...")
                time.sleep(2)
                continue
        except NetworkError as e:
            print(f"✗ Network error for {recipient_email} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print(f"⚠ Retrying due to network error...")
                time.sleep(5)  # Longer delay for network issues
                continue
        except Exception as e:
            print(f"✗ Unexpected error for {recipient_email} (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                print(f"⚠ Retrying due to unexpected error...")
                time.sleep(2)
                continue
    
    print(f"✗ Failed to send email to {recipient_email} after {max_retries} attempts")
    return False


def _send_with_authentication(msg, recipient_email):
    """Send email using authentication manager with automatic fallback.
    
    Args:
        msg: Email message to send
        recipient_email: Recipient email address
        
    Returns:
        bool: True if sent successfully, False otherwise
        
    Raises:
        AuthenticationError: If authentication fails
        NetworkError: If network connection fails
    """
    server = None
    try:
        # Check if auth_manager is available
        if auth_manager is None:
            raise AuthenticationError("Authentication manager not initialized", None)
            
        # Get authentication manager (with fallback capability)
        current_manager = auth_manager.get_current_manager()
        
        # Ensure authentication
        if not current_manager.is_authenticated:
            success = current_manager.authenticate()
            if not success:
                # Try fallback if primary fails
                fallback_manager = auth_manager.get_fallback_manager()
                if fallback_manager and not fallback_manager.is_authenticated:
                    fallback_success = fallback_manager.authenticate()
                    if fallback_success:
                        current_manager = fallback_manager
                    else:
                        raise AuthenticationError("Both primary and fallback authentication failed", current_manager.provider)
                else:
                    raise AuthenticationError("Primary authentication failed and no fallback available", current_manager.provider)
        
        # Get access token/credentials
        access_token = current_manager.get_access_token()
        
        # Determine SMTP configuration based on provider
        provider = current_manager.provider
        if provider.name == "MICROSOFT_OAUTH":
            smtp_server = settings.smtp_server if settings else "smtp.office365.com"
            smtp_port = settings.smtp_port if settings else 587
        elif provider.name == "GMAIL_APP_PASSWORD":
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
        else:
            # Use default configuration
            smtp_server = settings.smtp_server if settings else "smtp.office365.com"
            smtp_port = settings.smtp_port if settings else 587
        
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        # Authenticate based on provider type
        sender_email = settings.sender_email if settings else "default@example.com"
        if provider.name == "MICROSOFT_OAUTH":
            # Use OAuth 2.0 authentication
            oauth_string = get_oauth_string(sender_email, access_token)
            auth_msg = f"\x00{sender_email}\x00{oauth_string}"
            server.docmd("AUTH", "XOAUTH2 " + base64.b64encode(auth_msg.encode()).decode())
        elif provider.name == "GMAIL_APP_PASSWORD":
            # Use app password authentication
            gmail_email = current_manager._config.get("gmail_sender_email", sender_email)
            server.login(gmail_email, access_token)
        else:
            raise AuthenticationError(f"Unsupported authentication provider: {provider.name}", provider)
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        raise InvalidCredentialsError(f"SMTP authentication failed: {e}", current_manager.provider if 'current_manager' in locals() else None)
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
        raise NetworkError(f"SMTP connection failed: {e}", current_manager.provider if 'current_manager' in locals() else None)
    except smtplib.SMTPException as e:
        raise AuthenticationError(f"SMTP error: {e}", current_manager.provider if 'current_manager' in locals() else None)
    finally:
        if server:
            try:
                server.quit()
            except:
                pass  # Ignore errors when closing connection


def read_contacts_from_csv(csv_file):
    """Read contacts from CSV file"""
    contacts = []

    try:
        with open(csv_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                contact_name = row.get("Primary Contact Name", "").strip()
                email = row.get("Email", "").strip()

                if email and "@" in email:  # Basic email validation
                    first_name = get_first_name(contact_name)
                    contacts.append(
                        {
                            "email": email,
                            "first_name": first_name,
                            "contact_name": contact_name,
                        }
                    )

        print(f"Found {len(contacts)} valid contacts")
        return contacts

    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return []


def send_batch_emails(contacts, start_index, batch_size):
    """Send a batch of emails"""
    end_index = min(start_index + batch_size, len(contacts))
    batch = contacts[start_index:end_index]

    print(
        f"\n--- Sending batch {start_index//batch_size + 1} ({start_index+1}-{end_index}) ---"
    )

    successful_sends = 0

    for contact in batch:
        if send_email(contact["email"], contact["first_name"]):
            successful_sends += 1
        time.sleep(1)  # Small delay between emails in a batch

    return successful_sends, end_index


def main():
    # Check if authentication manager is available
    if auth_manager is None:
        print("Authentication failed. Cannot proceed with email campaign.")
        sys.exit(1)
    
    # Read contacts from CSV
    csv_file = "tier_i_tier_ii_emails_verified.csv"
    contacts = read_contacts_from_csv(csv_file)

    if not contacts:
        print("No contacts found. Exiting.")
        return

    print("\n" + "=" * 60)
    print("EMAIL CAMPAIGN SETUP")
    print("=" * 60)
    print(f"Total contacts: {len(contacts)}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Delay between batches: {DELAY_MINUTES} minutes")
    print("=" * 60)

    # Show first few contacts as preview
    print("\nPREVIEW OF FIRST 5 CONTACTS:")
    for i, contact in enumerate(contacts[:5]):
        print(
            f"{i+1}. {contact['contact_name']} ({contact['first_name']}) - {contact['email']}"
        )

    if len(contacts) > 5:
        print("...")

    # Check if we should proceed
    proceed = input("\nProceed with sending? (y/n): ").lower().strip()
    if proceed != "y":
        print("Campaign cancelled.")
        return

    # First, send test email to dwmaginn@gmail.com
    print("\n" + "=" * 60)
    print("SENDING TEST EMAIL")
    print("=" * 60)

    test_recipient = "dwmaginn@gmail.com"
    test_contact = next((c for c in contacts if c["email"] == test_recipient), None)

    if test_contact:
        first_name = test_contact["first_name"]
    else:
        first_name = "David"  # Fallback

    print(f"Sending test email to: {test_recipient} (First name: {first_name})")
    test_sent = send_email(test_recipient, first_name)

    if not test_sent:
        print("Test email failed. Please check your email configuration.")
        return

    print("✓ Test email sent successfully!")

    # Wait for user approval before proceeding with full campaign
    print("\n" + "=" * 60)
    print("WAITING FOR APPROVAL")
    print("=" * 60)
    print("Test email sent successfully.")
    print(
        "Please check your inbox and reply to confirm you want to proceed with the full campaign."
    )
    print("The full campaign will send emails to all contacts in the list.")

    approval = (
        input("Do you want to proceed with the full campaign? (y/n): ").lower().strip()
    )
    if approval != "y":
        print("Full campaign cancelled. Only test email was sent.")
        return

    # Proceed with full campaign
    print("\n" + "=" * 60)
    print("STARTING FULL CAMPAIGN")
    print("=" * 60)

    total_sent = 0
    start_index = 0

    while start_index < len(contacts):
        successful_sends, next_index = send_batch_emails(
            contacts, start_index, BATCH_SIZE
        )
        total_sent += successful_sends
        start_index = next_index

        # If there are more batches to send, wait for the specified delay
        if start_index < len(contacts):
            print(
                f"\n⏳ Sent {successful_sends} emails. Waiting {DELAY_MINUTES} minutes before next batch..."
            )
            time.sleep(DELAY_MINUTES * 60)  # Convert minutes to seconds

    print("\n" + "=" * 60)
    print("CAMPAIGN COMPLETED")
    print("=" * 60)
    print(f"Total emails attempted: {len(contacts)}")
    print(f"Total emails sent successfully: {total_sent}")
    print("=" * 60)


if __name__ == "__main__":
    main()
