# TierII Email Campaign Tool

A Python-based email campaign tool designed for bulk email sending using the MailerSend API. This tool provides personalized email campaigns with rate limiting, progress tracking, and comprehensive reporting.

## 🌿 Project Overview

This project is a robust email marketing solution that reads contact data from CSV files and sends personalized emails using the MailerSend API. It features configurable rate limiting, batch processing, real-time progress tracking, and detailed campaign reporting.

## 📋 Features

- **MailerSend API Integration**: Modern, reliable email delivery service with high deliverability
- **Personalized Emails**: Automatically extracts first names from contact data for personalization
- **Rate Limiting**: Configurable batch processing with delays to respect API limits
- **CSV Integration**: Reads contact data from CSV files with flexible column mapping
- **Progress Tracking**: Real-time progress bars with colored console output
- **Error Handling**: Robust error handling with detailed logging and recovery
- **HTML Reports**: Comprehensive campaign results with success metrics
- **Configuration-Driven**: JSON-based configuration for emails and rate limiting

## 📁 Project Structure

```
├── src/                                # Source code directory
│   ├── __init__.py                    # Package initialization
│   ├── main.py                        # Main campaign script and entry point
│   └── utils/                         # Utility modules
│       ├── __init__.py               # Utils package initialization
│       ├── csv_reader.py             # CSV parsing and contact extraction
│       ├── json_reader.py            # Configuration file loading
│       └── report_generator.py       # HTML report generation
├── tests/                             # Test suite (unit & integration)
│   ├── __init__.py                   # Test package initialization
│   ├── conftest.py                   # Pytest configuration and fixtures
│   ├── test_csv_reader.py            # CSV reader tests
│   ├── test_main.py                  # Main functionality tests
│   └── test_report_generator.py      # Report generator tests
├── templates/                         # Email and report templates
│   ├── email_template.html           # HTML email template
│   ├── report_template.html          # Campaign report template
│   └── sample_template.html          # Sample template for reference
├── docs/                             # Documentation
│   ├── README.md                     # Documentation index
│   ├── user-documentation.md         # User guide and manual
│   └── technical-documentation.md    # Technical reference
├── .github/workflows/                # GitHub Actions CI/CD
│   └── ci.yml                        # Continuous integration workflow
├── email_config.json                # Email campaign configuration
├── rate_config.json                  # Rate limiting configuration
├── requirements.txt                  # Python dependencies
├── pyproject.toml                    # Python project configuration
├── pytest.ini                       # Pytest configuration
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore rules
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
   # Clone from your repository or download the project
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
   ```
   
   ⚠️ **SECURITY WARNING**: Never commit `.env` files to version control!

5. **Test your setup**
   ```bash
   python -m pytest tests/
   ```

### Running the Campaign

1. **Configure your campaign**
   
   Edit `email_config.json` to set your campaign details:
   ```json
   {
       "subject": "Your Email Subject",
       "body": "Email body with {name} placeholder",
       "html": "templates/email_template.html",
       "attachments": [],
       "contacts": "data/test/testdata.csv"
   }
   ```

2. **Configure rate limiting**
   
   Edit `rate_config.json` to set your sending limits:
   ```json
   {
       "batch_size": 10,
       "cooldown": 60,
       "individual_cooldown": 7
   }
   ```

3. **Launch the email campaign**
   ```bash
   python -m src.main
   ```

The script will:
- Load contacts from the configured CSV file
- Show a preview of contacts to be processed
- Process emails in batches with configured delays
- Generate a detailed HTML report of the campaign results
- Log all activities with colored console output

## ⚙️ Configuration Options

### Email Configuration (`email_config.json`)

- `subject`: Email subject line
- `body`: Plain text email body (supports `{name}` placeholder)
- `html`: Path to HTML email template
- `attachments`: Array of file paths to attach
- `contacts`: Path to CSV file containing contact data

### Rate Limiting Configuration (`rate_config.json`)

- `batch_size`: Number of emails to send per batch
- `cooldown`: Seconds to wait between batches
- `individual_cooldown`: Seconds to wait between individual emails

### Environment Variables

- `TIERII_SENDER_EMAIL`: Your verified sender email address
- `TIERII_MAILERSEND_API_TOKEN`: Your MailerSend API token

## 📊 CSV Data Format

The tool expects CSV files with the following columns:

### Required Columns
- **Email**: Valid email address for the recipient
- **Primary Contact Name**: Full name for personalization (e.g., "John Smith")

### Optional Columns
- License Number, Entity Name, Business Website
- Address fields (Street, City, State, ZIP)
- License Type, Status, Expiration Date
- Any additional business data

### Data Validation
- Email addresses are validated for proper format
- Names are automatically parsed to extract first names
- Invalid or empty emails are skipped with logging
- Special characters in names are handled gracefully

## 🔒 Security & Compliance

### ⚠️ CRITICAL SECURITY WARNINGS

**Environment Variables & Secrets Management:**
- **NEVER commit `.env` files to version control** - they contain sensitive credentials
- **NEVER hardcode secrets** in source code or configuration files
- **Use unique, strong API tokens** and rotate them regularly
- **Limit access** to `.env` files using appropriate file permissions
- **Use secure secret management** for production deployments

**MailerSend API Security:**
- **Protect your API token** - treat it like a password
- **Use domain verification** to prevent unauthorized sending
- **Monitor API usage** and revoke compromised tokens immediately

**Development Security:**
- **Use separate credentials** for development, staging, and production
- **Never share credentials** via email, chat, or other insecure channels
- **Clean up test data** and temporary credentials after development
- **Review code changes** for accidentally committed secrets before merging

### Data Protection
- MailerSend API authentication with secure token-based access
- Environment-based secure credential handling
- Rate limiting to prevent abuse and respect API limits
- Input validation and sanitization for all contact data

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

### Test Individual Components
Test specific modules:
```bash
python -m pytest tests/test_csv_reader.py -v
python -m pytest tests/test_main.py -v
python -m pytest tests/test_report_generator.py -v
```

## 📈 Campaign Analytics

The campaign tool provides comprehensive feedback:
- Total contacts loaded and processed
- Batch processing progress with visual indicators
- Successful/failed email counts with detailed logging
- Rate limiting status and timing information
- Campaign completion summary with metrics
- HTML report generation with detailed results

## 🛠️ Troubleshooting

### Common Issues

1. **MailerSend API Errors**
   - Verify your API token is correct and active
   - Check that your sender domain is verified in MailerSend
   - Ensure you haven't exceeded your sending limits

2. **Email Sending Failures**
   - Check internet connection stability
   - Verify MailerSend API status
   - Review rate limiting configuration
   - Check sender domain verification status

3. **CSV Data Issues**
   - Validate CSV file format and encoding
   - Check for missing required columns (Email, Primary Contact Name)
   - Verify contact name formatting
   - Ensure file path in `email_config.json` is correct

4. **Configuration Issues**
   - Verify `email_config.json` and `rate_config.json` syntax
   - Check file paths in configuration files
   - Ensure environment variables are properly set

### Getting Help

Run the test suite to validate your configuration:
```bash
python -m pytest tests/ -v
```

Check the logs directory for detailed error information and campaign reports.

## 📝 License

This project is intended for legitimate business-to-business communications. Users are responsible for compliance with all applicable laws and regulations.

## 🤝 Contributing

Contributions should focus on:
- Improving email deliverability and reliability
- Enhancing data validation and error handling
- Adding analytics and reporting features
- Strengthening security measures
- Expanding template and personalization options

## ⚠️ Disclaimer

This tool is designed for legitimate business communications. Users must:
- Comply with all applicable laws and regulations
- Respect recipient preferences and opt-out requests
- Use the tool responsibly and ethically
- Maintain data privacy and security standards
- Follow email marketing best practices and anti-spam regulations

---

**Note**: This project provides a flexible foundation for email campaigns. Ensure compliance with all local, state, and federal regulations when using this tool for commercial purposes.
