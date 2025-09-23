# Email Configuration for Microsoft 365 / Outlook
SENDER_EMAIL = "david@honestpharmco.com"
SMTP_SERVER = "smtp.office365.com"  # Microsoft 365 SMTP server
SMTP_PORT = 587  # TLS port for Microsoft 365

# OAuth 2.0 Configuration for Exchange Online SMTP
# You need to register an Azure AD app and get these credentials
# Follow the instructions in the Microsoft Learn article
TENANT_ID = "your-tenant-id-here"  # Your Azure AD tenant ID
CLIENT_ID = "your-client-id-here"  # Your Azure AD app client ID
CLIENT_SECRET = "your-client-secret-here"  # Your Azure AD app client secret

# Legacy Basic Auth (will be deprecated) - keep for reference
# SENDER_PASSWORD = "Pharmco1!"  # Microsoft 365 password

# Rate limiting settings (these can be imported by the main script)
BATCH_SIZE = 10
DELAY_MINUTES = 3
