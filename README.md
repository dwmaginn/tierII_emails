# Cannabis Industry Email Campaign Tool

A Python-based email campaign tool designed for reaching out to licensed cannabis businesses in New York State. This tool uses OAuth 2.0 authentication with Microsoft 365 to send personalized emails to Tier I and Tier II cannabis license holders.

## 🌿 Project Overview

This project contains a comprehensive email marketing solution for the cannabis industry, specifically targeting licensed processors and microbusinesses in New York State. The tool reads from a verified CSV database of cannabis license holders and sends personalized outreach emails.

## 📋 Features

- **OAuth 2.0 Authentication**: Modern, secure authentication with Microsoft 365/Exchange Online
- **Personalized Emails**: Automatically extracts first names for personalized greetings
- **Rate Limiting**: Built-in batch processing with configurable delays to respect email limits
- **CSV Integration**: Reads contact data from verified cannabis license databases
- **Test Mode**: Send test emails before launching full campaigns
- **Progress Tracking**: Real-time feedback on email sending progress
- **Error Handling**: Robust error handling with detailed logging

## 📁 Project Structure

```
├── config.py                           # Email and OAuth configuration
├── email_campaign.py                   # Main email campaign script
├── oauth_setup_guide.py               # Step-by-step OAuth setup guide
├── tier_i_tier_ii_emails_verified.csv # Verified cannabis business contacts
├── test_csv_reader.py                  # CSV data validation script
├── test_email_settings.py             # Email configuration testing
├── test_oauth_smtp.py                  # OAuth authentication testing
├── requirements.txt                    # Python dependencies
└── README.md                          # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Microsoft 365 business account
- Azure AD application with SMTP permissions

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/cannabis-email-campaign.git
   cd cannabis-email-campaign
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure OAuth 2.0**
   
   Run the setup guide to configure Microsoft 365 OAuth:
   ```bash
   python oauth_setup_guide.py
   ```
   
   Follow the detailed instructions to:
   - Enable SMTP AUTH in Microsoft 365
   - Register an Azure AD application
   - Configure API permissions
   - Generate client credentials

4. **Configure environment variables**
   
   Copy the example environment file and configure your credentials:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your actual credentials:
   ```bash
   # Required OAuth credentials
   TIERII_SENDER_EMAIL=your-email@domain.com
   TIERII_SMTP_SERVER=smtp.office365.com
   TIERII_TENANT_ID=your-tenant-id
   TIERII_CLIENT_ID=your-client-id
   TIERII_CLIENT_SECRET=your-client-secret
   TIERII_EMAIL_SUBJECT="Your Email Subject"
   ```
   
   ⚠️ **SECURITY WARNING**: Never commit `.env` files to version control!

5. **Test your setup**
   ```bash
   python test_email_settings.py
   ```

### Running the Campaign

1. **Verify your contact data**
   ```bash
   python test_csv_reader.py
   ```

2. **Launch the email campaign**
   ```bash
   python email_campaign.py
   ```

The script will:
- Load contacts from the CSV file
- Show a preview of contacts
- Send a test email for verification
- Wait for your approval before sending to all contacts
- Process emails in batches with configurable delays

## ⚙️ Configuration Options

### Email Settings (`config.py`)

- `SENDER_EMAIL`: Your Microsoft 365 email address
- `SMTP_SERVER`: Microsoft 365 SMTP server (smtp.office365.com)
- `SMTP_PORT`: SMTP port (587 for TLS)
- `BATCH_SIZE`: Number of emails per batch (default: 10)
- `DELAY_MINUTES`: Minutes to wait between batches (default: 3)

### OAuth Credentials

- `TENANT_ID`: Your Azure AD tenant ID
- `CLIENT_ID`: Your Azure AD application client ID
- `CLIENT_SECRET`: Your Azure AD application client secret

## 📊 Data Source

The project includes a verified CSV database (`tier_i_tier_ii_emails_verified.csv`) containing:

- **120 verified contacts** from licensed NY cannabis businesses
- **License information**: License numbers, types, and status
- **Business details**: Entity names, addresses, and operational status
- **Contact information**: Primary contact names and email addresses
- **Business categories**: Tier types and processor classifications

### Data Fields

- License Number, Type, and Status
- Entity Name and Address
- Primary Contact Name and Email
- Business Website and Operational Status
- Tier Type and Processor Type

## 🔒 Security & Compliance

### ⚠️ CRITICAL SECURITY WARNINGS

**Environment Variables & Secrets Management:**
- **NEVER commit `.env` files to version control** - they contain sensitive credentials
- **NEVER hardcode secrets** in source code or configuration files
- **Use unique, strong client secrets** and rotate them regularly
- **Limit access** to `.env` files using appropriate file permissions (600/640)
- **Use Azure Key Vault** or similar secret management for production deployments
- **Audit access** to configuration files and credentials regularly

**OAuth 2.0 Security:**
- **Verify redirect URIs** are properly configured in Azure AD
- **Use least privilege** - only grant necessary API permissions
- **Monitor token usage** and revoke compromised tokens immediately
- **Enable MFA** on accounts with OAuth application access

**Development Security:**
- **Use separate credentials** for development, staging, and production
- **Never share credentials** via email, chat, or other insecure channels
- **Clean up test data** and temporary credentials after development
- **Review code changes** for accidentally committed secrets before merging

### Data Protection
- OAuth 2.0 authentication (no password storage)
- Automatic token refresh and management
- Environment-based secure credential handling
- Rate limiting to prevent abuse
- Input validation and sanitization

### Email Compliance
- Personalized, relevant business communications
- Clear sender identification
- Professional email content
- Respect for recipient preferences

### Legal Considerations
- Targets only licensed cannabis businesses
- Business-to-business communications
- Compliant with cannabis industry regulations
- Follows email marketing best practices

## 🧪 Testing Scripts

### `test_csv_reader.py`
Validates the CSV data structure and contact information:
```bash
python test_csv_reader.py
```

### `test_email_settings.py`
Tests email configuration and OAuth authentication:
```bash
python test_email_settings.py
```

### `test_oauth_smtp.py`
Specifically tests OAuth 2.0 SMTP authentication:
```bash
python test_oauth_smtp.py
```

## 📈 Usage Analytics

The campaign tool provides real-time feedback:
- Total contacts loaded
- Batch processing progress
- Successful/failed email counts
- Rate limiting status
- Campaign completion summary

## 🛠️ Troubleshooting

### Common Issues

1. **OAuth Authentication Errors**
   - Verify SMTP AUTH is enabled in Microsoft 365
   - Check API permissions in Azure AD
   - Ensure client credentials are correct

2. **Email Sending Failures**
   - Check internet connection
   - Verify SMTP server settings
   - Review rate limiting configuration

3. **CSV Data Issues**
   - Validate CSV file format
   - Check for missing email addresses
   - Verify contact name formatting

### Getting Help

Run the OAuth setup guide for detailed configuration instructions:
```bash
python oauth_setup_guide.py
```

## 📝 License

This project is intended for legitimate business-to-business communications within the legal cannabis industry. Users are responsible for compliance with all applicable laws and regulations.

## 🤝 Contributing

This is a specialized tool for cannabis industry outreach. Contributions should focus on:
- Improving email deliverability
- Enhancing data validation
- Adding analytics features
- Strengthening security measures

## ⚠️ Disclaimer

This tool is designed for legitimate business communications with licensed cannabis operators. Users must:
- Comply with all applicable laws and regulations
- Respect recipient preferences and opt-out requests
- Use the tool responsibly and ethically
- Maintain data privacy and security standards

---

**Note**: This project is specifically designed for the New York State cannabis industry and targets only licensed businesses. Ensure compliance with all local, state, and federal regulations when using this tool.
