#!/usr/bin/env python3
"""
Test OAuth 2.0 SMTP Authentication for Microsoft 365

This script tests the OAuth 2.0 authentication setup for SMTP email sending.
Make sure you've completed the OAuth setup steps before running this test.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import requests
from datetime import datetime, timedelta
import sys

# Import configuration
try:
    from src.config.settings import TierIISettings
    settings = TierIISettings()
    SENDER_EMAIL = settings.sender_email
    SMTP_SERVER = settings.smtp_server
    SMTP_PORT = settings.smtp_port
    TENANT_ID = settings.tenant_id
    CLIENT_ID = settings.client_id
    CLIENT_SECRET = settings.client_secret
except ImportError as e:
    print(
        f"Error: Could not import settings: {e}. Please ensure src.config.settings is available."
    )
    sys.exit(1)
except Exception as e:
    print(
        f"Error: Could not load configuration: {e}. Please check your environment variables."
    )
    sys.exit(1)


class OAuthTokenManager:
    def __init__(self):
        self.access_token = None
        self.token_expiry = None
        self.scope = "https://outlook.office365.com/.default"

    def get_access_token(self):
        """Get a valid access token, refreshing if necessary"""
        if (
            self.access_token
            and self.token_expiry
            and datetime.now() < self.token_expiry
        ):
            return self.access_token

        # Request new token
        token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        token_data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": self.scope,
            "grant_type": "client_credentials",
        }

        try:
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            token_response = response.json()

            self.access_token = token_response["access_token"]
            # Set expiry to 5 minutes before actual expiry for safety
            expires_in = token_response.get("expires_in", 3600) - 300
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            print("✓ OAuth token obtained successfully")
            return self.access_token

        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to obtain OAuth token: {e}")
            if hasattr(e, "response") and e.response:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise


def get_oauth_string(username, access_token):
    """Generate OAuth string for SMTP authentication"""
    auth_string = f"user={username}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_string.encode()).decode()


def test_oauth_smtp():
    """Test OAuth SMTP connection and authentication"""
    token_manager = OAuthTokenManager()

    try:
        print("=" * 80)
        print("TESTING OAUTH 2.0 SMTP AUTHENTICATION")
        print("=" * 80)
        print(f"SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
        print(f"Email: {SENDER_EMAIL}")
        print()

        # Test 1: Get OAuth token
        print("Step 1: Obtaining OAuth access token...")
        try:
            access_token = token_manager.get_access_token()
            print("✓ OAuth token obtained successfully")
        except Exception as e:
            print(f"✗ Failed to get OAuth token: {e}")
            return False

        # Test 2: Connect to SMTP server
        print("\nStep 2: Connecting to SMTP server...")
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            print("✓ SMTP connection established")
        except Exception as e:
            print(f"✗ SMTP connection failed: {e}")
            return False

        # Test 3: Start TLS
        print("\nStep 3: Starting TLS...")
        try:
            server.starttls()
            print("✓ TLS started successfully")
        except Exception as e:
            print(f"✗ TLS failed: {e}")
            server.quit()
            return False

        # Test 4: OAuth Authentication
        print("\nStep 4: Authenticating with OAuth 2.0...")
        try:
            oauth_string = get_oauth_string(SENDER_EMAIL, access_token)
            auth_msg = f"\x00{SENDER_EMAIL}\x00{oauth_string}"
            server.docmd(
                "AUTH", "XOAUTH2 " + base64.b64encode(auth_msg.encode()).decode()
            )
            print("✓ OAuth authentication successful")
        except Exception as e:
            print(f"✗ OAuth authentication failed: {e}")
            server.quit()
            return False

        # Test 5: Send test email
        print("\nStep 5: Sending test email...")
        try:
            msg = MIMEMultipart()
            msg["From"] = SENDER_EMAIL
            msg["To"] = SENDER_EMAIL  # Send to self for testing
            msg["Subject"] = "OAuth SMTP Test - Connection Verified"

            body = f"""OAuth SMTP Test successful!

Server: {SMTP_SERVER}:{SMTP_PORT}
Authentication: OAuth 2.0 (PASSED)
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This confirms your OAuth 2.0 SMTP configuration is working correctly!
You can now proceed with your email campaign."""

            msg.attach(MIMEText(body, "plain"))

            server.sendmail(SENDER_EMAIL, SENDER_EMAIL, msg.as_string())
            server.quit()
            print("✓ Test email sent successfully!")
        except Exception as e:
            print(f"✗ Test email failed: {e}")
            server.quit()
            return False

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("Your OAuth 2.0 SMTP configuration is working correctly.")
        print("You can now proceed with your email campaign.")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        return False


def main():
    print("OAuth 2.0 SMTP Test for Microsoft 365")
    print("This will test your OAuth configuration step by step.\n")

    # Check if credentials are properly configured
    missing_creds = []
    if TENANT_ID == "your-tenant-id-here":
        missing_creds.append("TENANT_ID")
    if CLIENT_ID == "your-client-id-here":
        missing_creds.append("CLIENT_ID")
    if CLIENT_SECRET == "your-client-secret-here":
        missing_creds.append("CLIENT_SECRET")

    if missing_creds:
        print("❌ Missing OAuth credentials in config.py:")
        for cred in missing_creds:
            print(f"   - {cred}")
        print("\nPlease update your config.py with the actual values from Azure AD.")
        print("Run the oauth_setup_guide.py for instructions.")
        return

    # Run the test
    success = test_oauth_smtp()

    if not success:
        print("\n❌ OAuth SMTP test failed!")
        print("\nTroubleshooting steps:")
        print(
            "1. Verify SMTP AUTH is enabled for your mailbox in Microsoft 365 admin center"
        )
        print("2. Check your Azure AD app registration and permissions")
        print("3. Ensure API permissions are granted with admin consent")
        print("4. Verify your credentials in config.py are correct")
        print("5. Make sure your tenant ID, client ID, and client secret are accurate")


if __name__ == "__main__":
    main()
