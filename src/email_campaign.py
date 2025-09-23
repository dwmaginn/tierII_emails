import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import sys
import os
import base64
import requests
import json
from datetime import datetime, timedelta

# Import configuration
try:
    from config import SENDER_EMAIL, SMTP_SERVER, SMTP_PORT, BATCH_SIZE, DELAY_MINUTES, TENANT_ID, CLIENT_ID, CLIENT_SECRET
except ImportError:
    print("Error: config.py file not found. Please create config.py with your OAuth credentials.")
    sys.exit(1)

# Email template
SUBJECT = "High-Quality Cannabis Available - Honest Pharmco"

# OAuth 2.0 token management
class OAuthTokenManager:
    def __init__(self):
        self.access_token = None
        self.token_expiry = None
        self.scope = "https://outlook.office365.com/.default"

    def get_access_token(self):
        """Get a valid access token, refreshing if necessary"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        # Request new token
        token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        token_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': self.scope,
            'grant_type': 'client_credentials'
        }

        try:
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            token_response = response.json()

            self.access_token = token_response['access_token']
            # Set expiry to 5 minutes before actual expiry for safety
            expires_in = token_response.get('expires_in', 3600) - 300
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            print("✓ OAuth token obtained successfully")
            return self.access_token

        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to obtain OAuth token: {e}")
            raise

# Global token manager instance
token_manager = OAuthTokenManager()

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
        titles = ['mr', 'mrs', 'ms', 'dr', 'prof', 'rev', 'sir', 'madam',
                 'mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'rev.', 'sir.', 'madam.']
        first_name_lower = first_name.lower()
        if first_name_lower in titles:
            return name_parts[1].strip() if len(name_parts) > 1 else "there"
        return first_name

    return "there"

def send_email(recipient_email, first_name):
    """Send email to a single recipient using OAuth 2.0 authentication"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = SUBJECT

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

        msg.attach(MIMEText(body, 'plain'))

        # Connect to SMTP server and send email with OAuth 2.0
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()

        # Get OAuth access token
        access_token = token_manager.get_access_token()

        # Generate OAuth string for SMTP
        oauth_string = get_oauth_string(SENDER_EMAIL, access_token)

        # Authenticate using XOAUTH2
        auth_msg = f"\x00{SENDER_EMAIL}\x00{oauth_string}"
        server.docmd("AUTH", "XOAUTH2 " + base64.b64encode(auth_msg.encode()).decode())

        # Send email
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, recipient_email, text)
        server.quit()

        print(f"✓ Email sent successfully to {recipient_email}")
        return True

    except Exception as e:
        print(f"✗ Failed to send email to {recipient_email}: {str(e)}")
        return False

def read_contacts_from_csv(csv_file):
    """Read contacts from CSV file"""
    contacts = []

    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                contact_name = row.get('Primary Contact Name', '').strip()
                email = row.get('Email', '').strip()

                if email and '@' in email:  # Basic email validation
                    first_name = get_first_name(contact_name)
                    contacts.append({
                        'email': email,
                        'first_name': first_name,
                        'contact_name': contact_name
                    })

        print(f"Found {len(contacts)} valid contacts")
        return contacts

    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return []

def send_batch_emails(contacts, start_index, batch_size):
    """Send a batch of emails"""
    end_index = min(start_index + batch_size, len(contacts))
    batch = contacts[start_index:end_index]

    print(f"\n--- Sending batch {start_index//batch_size + 1} ({start_index+1}-{end_index}) ---")

    successful_sends = 0

    for contact in batch:
        if send_email(contact['email'], contact['first_name']):
            successful_sends += 1
        time.sleep(1)  # Small delay between emails in a batch

    return successful_sends, end_index

def main():
    # Read contacts from CSV
    csv_file = "tier_i_tier_ii_emails_verified.csv"
    contacts = read_contacts_from_csv(csv_file)

    if not contacts:
        print("No contacts found. Exiting.")
        return

    print("\n" + "="*60)
    print("EMAIL CAMPAIGN SETUP")
    print("="*60)
    print(f"Total contacts: {len(contacts)}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Delay between batches: {DELAY_MINUTES} minutes")
    print("="*60)

    # Show first few contacts as preview
    print("\nPREVIEW OF FIRST 5 CONTACTS:")
    for i, contact in enumerate(contacts[:5]):
        print(f"{i+1}. {contact['contact_name']} ({contact['first_name']}) - {contact['email']}")

    if len(contacts) > 5:
        print("...")

    # Check if we should proceed
    proceed = input("\nProceed with sending? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Campaign cancelled.")
        return

    # First, send test email to dwmaginn@gmail.com
    print("\n" + "="*60)
    print("SENDING TEST EMAIL")
    print("="*60)

    test_recipient = "dwmaginn@gmail.com"
    test_contact = next((c for c in contacts if c['email'] == test_recipient), None)

    if test_contact:
        first_name = test_contact['first_name']
    else:
        first_name = "David"  # Fallback

    print(f"Sending test email to: {test_recipient} (First name: {first_name})")
    test_sent = send_email(test_recipient, first_name)

    if not test_sent:
        print("Test email failed. Please check your email configuration.")
        return

    print("✓ Test email sent successfully!")

    # Wait for user approval before proceeding with full campaign
    print("\n" + "="*60)
    print("WAITING FOR APPROVAL")
    print("="*60)
    print("Test email sent successfully.")
    print("Please check your inbox and reply to confirm you want to proceed with the full campaign.")
    print("The full campaign will send emails to all contacts in the list.")

    approval = input("Do you want to proceed with the full campaign? (y/n): ").lower().strip()
    if approval != 'y':
        print("Full campaign cancelled. Only test email was sent.")
        return

    # Proceed with full campaign
    print("\n" + "="*60)
    print("STARTING FULL CAMPAIGN")
    print("="*60)

    total_sent = 0
    start_index = 0

    while start_index < len(contacts):
        successful_sends, next_index = send_batch_emails(contacts, start_index, BATCH_SIZE)
        total_sent += successful_sends
        start_index = next_index

        # If there are more batches to send, wait for the specified delay
        if start_index < len(contacts):
            print(f"\n⏳ Sent {successful_sends} emails. Waiting {DELAY_MINUTES} minutes before next batch...")
            time.sleep(DELAY_MINUTES * 60)  # Convert minutes to seconds

    print("\n" + "="*60)
    print("CAMPAIGN COMPLETED")
    print("="*60)
    print(f"Total emails attempted: {len(contacts)}")
    print(f"Total emails sent successfully: {total_sent}")
    print("="*60)

if __name__ == "__main__":
    main()