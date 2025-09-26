# Cannabis Industry Email Campaign Tool

A Python-based email campaign tool designed for reaching out to licensed cannabis businesses in New York State. This tool uses MailerSend API for reliable email delivery to Tier I and Tier II cannabis license holders.

## 🌿 Project Overview

This project contains a comprehensive email marketing solution for the cannabis industry, specifically targeting licensed processors and microbusinesses in New York State. The tool reads from a verified CSV database of cannabis license holders and sends personalized outreach emails using the MailerSend API.

## 📋 Features

- **MailerSend API Integration**: Modern, reliable email delivery service with high deliverability
- **Personalized Emails**: Automatically extracts first names for personalized greetings
- **Rate Limiting**: Built-in batch processing with configurable delays to respect email limits
- **CSV Integration**: Reads contact data from verified cannabis license databases
- **Test Mode**: Send test emails before launching full campaigns
- **Progress Tracking**: Real-time feedback on email sending progress
- **Error Handling**: Robust error handling with detailed logging

## 📁 Project Structure

```
├── src/                                # Source code directory
│   ├── auth/                          # Authentication modules
│   ├── config/                        # Configuration management
│   ├── utils/                         # Utility functions
│   └── email_campaign.py              # Main campaign script
├── tests/                             # Test suite (unit & integration)
├── data/contacts/                     # Contact CSV files
├── templates/                         # Email templates
├── scripts/                           # Helper scripts
├── requirements.txt                   # Python dependencies
└── README.md                         # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- MailerSend account with API access
- Valid sender domain configured in MailerSend

### Installation

1. **Clone the repository**
   ```bash
   # Clone from your actual repository or download the project
   cd tierII_emails
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure MailerSend API**
   
   Sign up for a MailerSend account at https://www.mailersend.com/
   - Create an API token in your MailerSend dashboard
   - Verify your sender domain
   - Note your API token for configuration

4. **Configure environment variables**
   
   Copy the example environment file and configure your credentials:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your actual credentials:
   ```bash
   # Required MailerSend Configuration
   TIERII_SENDER_EMAIL="your-verified-sender@yourdomain.com"
   TIERII_MAILERSEND_API_TOKEN="your_mailersend_api_token_here"

   # Optional Configuration (with defaults)
   TIERII_EMAIL_TEMPLATE_PATH=templates/email_template.html  # Optional
   TIERII_CAMPAIGN_BATCH_SIZE=50                             # Default: 50
   TIERII_CAMPAIGN_DELAY_MINUTES=5                           # Default: 5 minutes
   TIERII_TEST_FALLBACK_FIRST_NAME=Friend                    # Default: Friend
   TIERII_TEST_CSV_FILENAME=data/contacts/tier_i_tier_ii_emails_verified.csv
   ```
   
   ⚠️ **SECURITY WARNING**: Never commit `.env` files to version control!

5. **Test your setup**
   ```bash
   python -m pytest tests/
   ```

6. **Verify installation**
   ```bash
   # Verify installation
   python -c "import src.email_campaign; print('Installation successful')"
   ```

### Running the Campaign

1. **Verify your contact data**
   ```bash
   python scripts/t_csv_reader.py
   ```

2. **Launch the email campaign**
   ```bash
   python src/email_campaign.py
   ```

The script will:
- Load contacts from the CSV file
- Show a preview of contacts
- Send a test email for verification
- Wait for your approval before sending to all contacts
- Process emails in batches with configurable delays

## ⚙️ Configuration Options

### MailerSend Settings

- `TIERII_SENDER_EMAIL`: Your verified sender email address
- `TIERII_MAILERSEND_API_TOKEN`: Your MailerSend API token
- `TIERII_SENDER_NAME`: Display name for email sender
- `TIERII_CAMPAIGN_BATCH_SIZE`: Number of emails per batch (default: 50)
- `TIERII_CAMPAIGN_DELAY_MINUTES`: Minutes to wait between batches (default: 5)
- `TIERII_EMAIL_TEMPLATE_PATH`: Path to email template (default: templates/email_template.html)
- `TIERII_TEST_FALLBACK_FIRST_NAME`: Default first name for personalization (default: Friend)
- `TIERII_TEST_CSV_FILENAME`: Path to CSV file (default: data/contacts/tier_i_tier_ii_emails_verified.csv)

## 📊 Data Source

The project includes a verified CSV database (`tier_i_tier_ii_emails_verified.csv`) containing:

- **119 verified contacts** from licensed NY cannabis businesses
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
- **Use unique, strong API tokens** and rotate them regularly
- **Limit access** to `.env` files using appropriate file permissions (600/640)
- **Use secure secret management** for production deployments
- **Audit access** to configuration files and credentials regularly

**MailerSend API Security:**
- **Protect your API token** - treat it like a password
- **Use domain verification** to prevent unauthorized sending
- **Monitor API usage** and revoke compromised tokens immediately
- **Enable webhook security** for delivery tracking

**Development Security:**
- **Use separate credentials** for development, staging, and production
- **Never share credentials** via email, chat, or other insecure channels
- **Clean up test data** and temporary credentials after development
- **Review code changes** for accidentally committed secrets before merging

### Data Protection
- MailerSend API authentication (secure token-based access)
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

## 🧪 Testing

### Run Test Suite
Run the complete test suite to validate functionality:
```bash
python -m pytest tests/ -v
```

### Run with Coverage
Generate test coverage reports:
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Test CSV Data
Validate contact data structure:
```bash
python scripts/t_csv_reader.py
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

1. **MailerSend API Errors**
   - Verify your API token is correct and active
   - Check that your sender domain is verified in MailerSend
   - Ensure you haven't exceeded your sending limits

2. **Email Sending Failures**
   - Check internet connection
   - Verify MailerSend API status
   - Review rate limiting configuration
   - Check sender domain verification status

3. **CSV Data Issues**
   - Validate CSV file format
   - Check for missing email addresses
   - Verify contact name formatting

### Getting Help

Run the test suite to validate your configuration:
```bash
python -m pytest tests/ -v
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
