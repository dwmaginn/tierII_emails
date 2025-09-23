#!/usr/bin/env python3
"""
OAuth 2.0 Setup Guide for Microsoft 365 SMTP Authentication

This guide helps you set up OAuth 2.0 authentication for sending emails through
Microsoft 365/Exchange Online SMTP, which is required due to the deprecation
of basic authentication.

Follow these steps to configure OAuth 2.0 for your email campaign:
"""

def print_step(step_num, title, description):
    """Print a formatted step"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print(f"{'='*60}")
    print(description)

def main():
    print("="*80)
    print("MICROSOFT 365 OAUTH 2.0 SETUP GUIDE")
    print("="*80)
    print("This guide will help you configure OAuth 2.0 authentication for SMTP")
    print("Follow each step carefully to enable modern authentication.\n")

    # Step 1: Enable SMTP AUTH
    print_step(1, "Enable SMTP AUTH for your mailbox",
        """1. Go to the Microsoft 365 admin center: https://admin.microsoft.com/
2. Navigate to Users > Active users
3. Select your user account (david@honestpharmco.com)
4. Click on "Mail" tab
5. Click "Manage email apps"
6. Check the box for "Authenticated SMTP"
7. Click "Save changes"

This enables SMTP AUTH for your specific mailbox.""")

    # Step 2: Register Azure AD App
    print_step(2, "Register an Azure AD Application",
        """1. Go to Azure Portal: https://portal.azure.com/
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Enter a name (e.g., "Email Campaign SMTP")
5. Select "Accounts in this organizational directory only"
6. Click "Register"

After registration, note down the:
- Application (client) ID
- Directory (tenant) ID""")

    # Step 3: Configure API Permissions
    print_step(3, "Configure API Permissions",
        """1. In your registered app, go to "API permissions"
2. Click "Add a permission"
3. Select "Microsoft Graph" > "Application permissions"
4. Add the following permissions:
   - SMTP.Send (under SMTP)

5. Click "Grant admin consent for [your organization]"

This gives your app permission to send emails via SMTP.""")

    # Step 4: Create Client Secret
    print_step(4, "Create Client Secret",
        """1. In your registered app, go to "Certificates & secrets"
2. Click "New client secret"
3. Enter a description (e.g., "SMTP Authentication")
4. Choose an expiration period
5. Click "Add"
6. IMPORTANT: Copy the secret value immediately (you won't see it again)

Note: The client secret is your CLIENT_SECRET in config.py""")

    # Step 5: Update Configuration
    print_step(5, "Update your config.py",
        """Update your config.py file with the following values:

TENANT_ID = "your-directory-tenant-id-here"  # From app registration
CLIENT_ID = "your-application-client-id-here"  # From app registration
CLIENT_SECRET = "your-client-secret-value-here"  # From step 4

Example:
TENANT_ID = "a1b2c3d4-e5f6-7890-abcd-1234567890ab"
CLIENT_ID = "1a2b3c4d-5e6f-7890-abcd-1234567890ab"
CLIENT_SECRET = "AbCdEfGhIjKlMnOpQrStUvWxYz1234567890"

Keep these credentials secure and never commit them to version control!""")

    # Step 6: Test Configuration
    print_step(6, "Test Your Configuration",
        """Run the test script to verify OAuth authentication:

python test_email_settings.py

This will test the OAuth connection and attempt to send a test email.

If you get authentication errors, double-check:
1. SMTP AUTH is enabled for your mailbox
2. API permissions are granted
3. Your credentials are correct""")

    # Additional Notes
    print(f"\n{'='*60}")
    print("IMPORTANT NOTES")
    print(f"{'='*60}")
    print("• OAuth tokens automatically refresh, so you don't need to worry about expiration")
    print("• The SMTP server should be: smtp.office365.com:587")
    print("• Your email address remains: david@honestpharmco.com")
    print("• Rate limits still apply - don't send too many emails too quickly")
    print("• Monitor your Azure AD app for any suspicious activity")
    print("• Consider setting up email sending limits in your Azure AD app if needed")

    print(f"\n{'='*60}")
    print("TROUBLESHOOTING")
    print(f"{'='*60}")
    print("Common issues:")
    print("1. 'SMTP AUTH not enabled' - Enable SMTP AUTH in Microsoft 365 admin center")
    print("2. 'Insufficient permissions' - Grant SMTP.Send permission and admin consent")
    print("3. 'Invalid credentials' - Check tenant ID, client ID, and client secret")
    print("4. 'Token expired' - Tokens auto-refresh, but check your app permissions")

    print(f"\n{'='*80}")
    print("Once you've completed these steps, your email campaign should work!")
    print("The OAuth authentication will handle token management automatically.")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()