import csv
import time
import sys
import os
import argparse
from datetime import datetime
from typing import Optional
import logging

# Import authentication components for MailerSend only
from auth.authentication_factory import authentication_factory
from auth.base_authentication_manager import (
    AuthenticationError,
    NetworkError,
    AuthenticationProvider
)

# Import configuration from settings module
from config.settings import load_settings

# Load settings
try:
    settings = load_settings()
except Exception as e:
    print(f"Error loading settings: {e}")
    sys.exit(1)

# Campaign configuration
BATCH_SIZE = settings.campaign_batch_size
DELAY_MINUTES = settings.campaign_delay_minutes

# Email subject
SUBJECT = "High-Quality Cannabis Available - Honest Pharmco"


class EmailCampaign:
    """Email campaign manager using MailerSend API."""
    
    def __init__(self, csv_file=None, batch_size=None, delay_minutes=None):
        self.csv_file = csv_file or settings.test_csv_filename
        self.batch_size = batch_size or settings.campaign_batch_size
        self.delay_minutes = delay_minutes or settings.campaign_delay_minutes
        self.contacts = []

    def load_contacts(self):
        """Load contacts from CSV file."""
        self.contacts = read_contacts_from_csv(self.csv_file)
        return len(self.contacts)

    def send_campaign(self):
        """Send email campaign in batches."""
        if not self.contacts:
            self.load_contacts()
        
        if not self.contacts:
            print("No contacts found. Exiting.")
            return 0
        
        total_sent = 0
        start_index = 0
        
        while start_index < len(self.contacts):
            end_index = min(start_index + self.batch_size, len(self.contacts))
            batch = self.contacts[start_index:end_index]
            
            print(f"\n--- Sending batch {start_index//self.batch_size + 1} ({start_index+1}-{end_index}) ---")
            
            batch_sent = 0
            for contact in batch:
                if send_email(contact["email"], contact["first_name"]):
                    batch_sent += 1
                time.sleep(1)  # Small delay between emails
            
            total_sent += batch_sent
            start_index = end_index
            
            # Wait between batches if more to send
            if start_index < len(self.contacts):
                time.sleep(self.delay_minutes * 60)
                
        return total_sent


def handle_authentication_with_exit(auth_manager, context_message: str = "authentication", success_exit_code: int = None):
    """
    Handle authentication with proper error handling and exit codes.
    
    Args:
        auth_manager: The authentication manager instance
        context_message: Context message for logging (e.g., "authentication", "Testing MailerSend authentication")
        success_exit_code: If provided, exit with this code on success (for test scenarios)
    """
    print(f"{context_message}...")
    try:
        auth_manager.authenticate()
        if success_exit_code is not None:
            print("✓ Authentication successful! MailerSend API key is valid.")
            print(f"✓ Sender email configured: {settings.sender_email}")
            sys.exit(success_exit_code)
        else:
            print("✓ Authentication successful!")
    except AuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
        sys.exit(1)
    except NetworkError as e:
        print(f"✗ Network error during authentication: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error during authentication: {e}")
        sys.exit(1)


def create_authentication_manager():
    """Create and configure the MailerSend authentication manager."""
    try:
        config = {
            "mailersend_api_token": settings.mailersend_api_token,
            "sender_email": settings.sender_email,
            "sender_name": settings.sender_name
        }
        
        return authentication_factory.create_manager(
            provider=AuthenticationProvider.MAILERSEND,
            config=config
        )
    except Exception as e:
        print(f"✗ Failed to initialize MailerSend authentication manager: {e}")
        raise

# Global authentication manager instance
try:
    auth_manager = create_authentication_manager()
    print(f"✓ MailerSend authentication manager initialized")
except Exception as e:
    print(f"Failed to initialize authentication manager: {e}")
    auth_manager = None


def get_first_name(contact_name):
    """Extract first name from contact name."""
    if not contact_name:
        return settings.test_fallback_first_name

    # Split by common delimiters and take first part
    name_parts = contact_name.split()
    if name_parts:
        first_name = name_parts[0].strip()
        # Remove common titles (with and without periods)
        titles = [
            "mr", "mrs", "ms", "dr", "prof", "rev", "sir", "madam",
            "mr.", "mrs.", "ms.", "dr.", "prof.", "rev.", "sir.", "madam.",
        ]
        first_name_lower = first_name.lower()
        if first_name_lower in titles:
            return name_parts[1].strip() if len(name_parts) > 1 else settings.test_fallback_first_name
        return first_name

    return settings.test_fallback_first_name


def load_email_template(first_name: str) -> str:
    """Load and personalize email template from external file.
    
    Args:
        first_name: First name to personalize the email
        
    Returns:
        Personalized HTML email content
    """
    try:
        # Check if custom template path is configured
        template_path = None
        try:
            template_path = getattr(settings, 'email_template_path', None)
            # Validate that template_path is a string (not a Mock object)
            if template_path and not isinstance(template_path, str):
                template_path = None
        except (AttributeError, TypeError):
            template_path = None
        
        if template_path and os.path.exists(template_path):
            template_file = template_path
        else:
            # Use default template
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            template_file = os.path.join(project_root, 'templates', 'email_template.html')
        
        if not os.path.exists(template_file):
            raise FileNotFoundError(f"Email template not found: {template_file}")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Personalize the template
        personalized_content = template_content.replace('{first_name}', first_name)
        
        return personalized_content
        
    except Exception as e:
        print(f"Warning: Could not load email template: {e}")
        # Fallback to simple text template
        return f"""Hi {first_name},

I hope this message finds you well. I wanted to reach out to you personally about an exciting opportunity that I believe could be of great interest to you.

At Honest Pharmco, we specialize in providing high-quality cannabis products that meet the highest standards of purity, potency, and safety.

Best regards,
David Maginn
Honest Pharmco
Email: contact@honestpharmco.com
Phone: (555) 123-4567
"""


def send_email(recipient_email, first_name, max_retries=3):
    """Send email to a single recipient using MailerSend API.
    
    Args:
        recipient_email: Email address to send to
        first_name: Personalized first name for email
        max_retries: Maximum number of retry attempts
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Process first name through get_first_name to handle fallback
    processed_first_name = get_first_name(first_name)
    
    for attempt in range(max_retries):
        try:
            # Load email template with personalized first name
            body = load_email_template(processed_first_name)

            # Use MailerSend authentication manager to send email
            if auth_manager is None:
                raise AuthenticationError("MailerSend authentication manager not initialized", None)
            
            # Send via MailerSend API
            success = auth_manager.send_email(
                to_email=recipient_email,
                to_name=processed_first_name,
                subject=SUBJECT,
                html_content=body
            )
            
            if success:
                print(f"✓ Email sent to {recipient_email} ({first_name})")
                return True
            else:
                print(f"✗ Failed to send email to {recipient_email} (attempt {attempt + 1})")
                
        except AuthenticationError as e:
            print(f"✗ Authentication error sending to {recipient_email}: {e}")
            if attempt == max_retries - 1:
                return False
            time.sleep(2 ** attempt)  # Exponential backoff
            
        except NetworkError as e:
            print(f"✗ Network error sending to {recipient_email}: {e}")
            if attempt == max_retries - 1:
                return False
            time.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            print(f"✗ Unexpected error sending to {recipient_email}: {e}")
            if attempt == max_retries - 1:
                return False
            time.sleep(2 ** attempt)  # Exponential backoff

    return False


def read_contacts_from_csv(csv_file):
    """Read contacts from CSV file."""
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
    """Send a batch of emails."""
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
    """Main function to run email campaign."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Email Campaign Manager')
    parser.add_argument('--test-csv', 
                       help='Path to test CSV file (e.g., /c:/Users/73spi/Work/tierII_emails/data/test/testdata.csv)',
                       type=str)
    parser.add_argument('--test-auth', 
                       help='Test authentication without sending emails',
                       action='store_true')
    parser.add_argument('--dry-run', 
                       help='Run in dry-run mode (only send test email, skip full campaign)',
                       action='store_true')
    args = parser.parse_args()
    
    # Check if authentication manager is available
    if auth_manager is None:
        print("MailerSend authentication failed. Cannot proceed with email campaign.")
        sys.exit(1)
    
    # Handle authentication testing
    if args.test_auth:
        handle_authentication_with_exit(auth_manager, "Testing MailerSend authentication", 0)
    
    # Determine which CSV file to use
    if args.test_csv:
        csv_file = args.test_csv
        print(f"Using test CSV file: {csv_file}")
    else:
        csv_file = settings.test_csv_filename
        print(f"Using default CSV file: {csv_file}")
    
    # Read contacts from CSV
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
    print(f"Using MailerSend API")
    print("=" * 60)

    # Show first few contacts as preview
    print("\nPREVIEW OF FIRST 5 CONTACTS:")
    for i, contact in enumerate(contacts[:5]):
        print(
            f"{i+1}. {contact['contact_name']} ({contact['first_name']}) - {contact['email']}"
        )

    if len(contacts) > 5:
        print("...")

    # Check if we should proceed (skip in dry-run mode)
    if not args.dry_run:
        proceed = input("\nProceed with sending? (y/n): ").lower().strip()
        if proceed != "y":
            print("Campaign cancelled.")
            return
    else:
        print("\nDry-run mode: Skipping user confirmation, proceeding to test email only.")

    # Authenticate with MailerSend before sending emails
    handle_authentication_with_exit(auth_manager, "Authenticating with MailerSend")

    # Send test email if test recipient is configured
    if settings.test_recipient_email:
        print("\n" + "=" * 60)
        print("SENDING TEST EMAIL")
        print("=" * 60)

        test_recipient = settings.test_recipient_email
        test_contact = next((c for c in contacts if c["email"] == test_recipient), None)

        if test_contact:
            first_name = test_contact["first_name"]
        else:
            first_name = settings.test_fallback_first_name

        print(f"Sending test email to: {test_recipient} (First name: {first_name})")
        test_sent = send_email(test_recipient, first_name)

        if not test_sent:
            print("Test email failed. Please check your MailerSend configuration.")
            return

        print("✓ Test email sent successfully!")

        # In dry-run mode, stop after test email
        if args.dry_run:
            print("\n" + "=" * 60)
            print("DRY-RUN MODE COMPLETED")
            print("=" * 60)
            print("Dry-run mode: Only test email was sent.")
            print("To run the full campaign, use the command without --dry-run flag.")
            return

        # Wait for user approval before proceeding with full campaign
        print("\n" + "=" * 60)
        print("WAITING FOR APPROVAL")
        print("=" * 60)
        print("Test email sent successfully.")
        print("Please check your inbox and reply to confirm you want to proceed with the full campaign.")
        print("The full campaign will send emails to all contacts in the list.")

        approval = input("Do you want to proceed with the full campaign? (y/n): ").lower().strip()
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
