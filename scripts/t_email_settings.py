import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

# Import configuration
try:
    from src.config.settings import TierIISettings
    settings = TierIISettings()
    SENDER_EMAIL = settings.sender_email
    SENDER_PASSWORD = settings.sender_password or ""  # May not be needed for OAuth
    SMTP_SERVER = settings.smtp_server
    SMTP_PORT = settings.smtp_port
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


def test_smtp_settings(server, port):
    """Test specific SMTP settings"""
    try:
        print(f"\n--- Testing {server}:{port} ---")
        print("Connecting to SMTP server...")

        server_conn = smtplib.SMTP(server, port, timeout=10)
        server_conn.starttls()
        print("Attempting login...")

        server_conn.login(SENDER_EMAIL, SENDER_PASSWORD)
        print("✅ SUCCESS: Authentication passed!")

        # Try to send a test email
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = SENDER_EMAIL
        msg["Subject"] = "SMTP Test - Connection Verified"

        body = f"""SMTP Test successful!
Server: {server}:{port}
Authentication: PASSED
Time: Connection test completed successfully.

This confirms your email settings work with these SMTP parameters."""

        msg.attach(MIMEText(body, "plain"))

        server_conn.sendmail(SENDER_EMAIL, SENDER_EMAIL, msg.as_string())
        server_conn.quit()

        print("✅ SUCCESS: Test email sent!")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION FAILED: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"❌ CONNECTION FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def main():
    print("=" * 80)
    print("MICROSOFT 365 SMTP TROUBLESHOOTING TEST")
    print("=" * 80)
    print("Testing different SMTP configurations for Microsoft 365...")

    # Test current settings first
    if test_smtp_settings(SMTP_SERVER, SMTP_PORT):
        print("\n" + "=" * 80)
        print("✅ PRIMARY CONFIGURATION WORKS!")
        print("You can proceed with the email campaign.")
        print("=" * 80)
        return

    # Try alternative Microsoft 365 SMTP settings
    print("\n" + "=" * 80)
    print("Trying alternative Microsoft 365 SMTP settings...")
    print("=" * 80)

    alternative_settings = [
        ("smtp-mail.outlook.com", 587),
        ("smtp-mail.outlook.com", 465),
        ("smtp.office365.com", 587),
        ("smtp.office365.com", 465),
        ("outlook.office365.com", 587),
        ("outlook.office365.com", 465),
    ]

    working_config = None
    for server, port in alternative_settings:
        if test_smtp_settings(server, port):
            working_config = (server, port)
            break

    print("\n" + "=" * 80)
    if working_config:
        server, port = working_config
        print("✅ ALTERNATIVE CONFIGURATION FOUND!")
        print(f"Working SMTP Server: {server}")
        print(f"Working SMTP Port: {port}")
        print("\nUpdate your config.py file with these settings:")
        print(f'SMTP_SERVER = "{server}"')
        print(f"SMTP_PORT = {port}")
    else:
        print("❌ NO WORKING CONFIGURATION FOUND")
        print("\nTroubleshooting steps:")
        print("1. Check if your Microsoft 365 account has 2FA enabled")
        print(
            "2. If 2FA is enabled, create an 'App Password' in your Microsoft account"
        )
        print("3. Verify your password is correct")
        print("4. Check if your account has SMTP restrictions")
        print("5. Try logging into https://outlook.com with your credentials")
    print("=" * 80)


def main():
    print("=" * 80)
    print("MICROSOFT 365 SMTP TROUBLESHOOTING TEST")
    print("=" * 80)
    print("Testing different SMTP configurations for Microsoft 365...")

    # Test current settings first
    if test_smtp_settings(SMTP_SERVER, SMTP_PORT):
        print("\n" + "=" * 80)
        print("✅ PRIMARY CONFIGURATION WORKS!")
        print("You can proceed with the email campaign.")
        print("=" * 80)
        return

    # Try alternative Microsoft 365 SMTP settings
    print("\n" + "=" * 80)
    print("Trying alternative Microsoft 365 SMTP settings...")
    print("=" * 80)

    alternative_settings = [
        ("smtp-mail.outlook.com", 587),
        ("smtp-mail.outlook.com", 465),
        ("smtp.office365.com", 587),
        ("smtp.office365.com", 465),
        ("outlook.office365.com", 587),
        ("outlook.office365.com", 465),
    ]

    working_config = None
    for server, port in alternative_settings:
        if test_smtp_settings(server, port):
            working_config = (server, port)
            break

    print("\n" + "=" * 80)
    if working_config:
        server, port = working_config
        print("✅ ALTERNATIVE CONFIGURATION FOUND!")
        print(f"Working SMTP Server: {server}")
        print(f"Working SMTP Port: {port}")
        print("\nUpdate your config.py file with these settings:")
        print(f'SMTP_SERVER = "{server}"')
        print(f"SMTP_PORT = {port}")
    else:
        print("❌ NO WORKING CONFIGURATION FOUND")
        print("\nTroubleshooting steps:")
        print("1. Check if your Microsoft 365 account has 2FA enabled")
        print(
            "2. If 2FA is enabled, create an 'App Password' in your Microsoft account"
        )
        print("3. Verify your password is correct")
        print("4. Check if your account has SMTP restrictions")
        print("5. Try logging into https://outlook.com with your credentials")
    print("=" * 80)


if __name__ == "__main__":
    main()
