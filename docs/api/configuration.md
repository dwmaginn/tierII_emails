# Configuration Reference

Complete reference for all configuration options, environment variables, and settings in the TierII Email Campaign system.

## 📋 Overview

The system uses environment-based configuration with Pydantic validation, providing type safety, default values, and comprehensive error handling.

## 🔧 Configuration Loading

### Configuration Sources (Priority Order)

1. **Environment Variables** (highest priority)
2. **`.env` File** (project root)
3. **Default Values** (lowest priority)

### Loading Process

```python
from src.config.settings import load_settings

# Load configuration with validation
settings = load_settings()

# Test mode loading (for development)
settings = load_settings(test_mode=True)
```

## 🌍 Environment Variables Reference

### Core Email Configuration (Required)

#### `TIERII_SENDER_EMAIL`
- **Type**: String (email address)
- **Required**: Yes
- **Description**: Email address used as sender for all outgoing emails
- **Validation**: Must be valid email format from verified domain
- **Example**: `noreply@yourdomain.com`

```bash
TIERII_SENDER_EMAIL=noreply@yourdomain.com
```

#### `TIERII_MAILERSEND_API_TOKEN`
- **Type**: String
- **Required**: Yes  
- **Description**: MailerSend API token for authentication
- **Security**: Never commit to version control
- **Format**: `ms_token_...` (MailerSend format)
- **Example**: `ms_token_abc123def456...`

```bash
TIERII_MAILERSEND_API_TOKEN=ms_token_your_actual_token_here
```

### Sender Configuration (Optional)

#### `TIERII_SENDER_NAME`
- **Type**: String
- **Required**: No
- **Default**: Derived from sender email domain
- **Description**: Display name for email sender
- **Example**: `TierII Campaign Team`

```bash
TIERII_SENDER_NAME=Your Company Name
```

### Campaign Settings

#### `TIERII_CAMPAIGN_BATCH_SIZE`
- **Type**: Integer
- **Required**: No
- **Default**: `50`
- **Range**: 1-100
- **Description**: Number of emails to send per batch
- **Use Case**: Rate limiting and performance optimization

```bash
TIERII_CAMPAIGN_BATCH_SIZE=25  # Smaller batches for careful sending
```

#### `TIERII_CAMPAIGN_DELAY_MINUTES`
- **Type**: Integer
- **Required**: No
- **Default**: `5`
- **Range**: 1-60
- **Description**: Minutes to wait between batches
- **Use Case**: Respect rate limits and avoid spam detection

```bash
TIERII_CAMPAIGN_DELAY_MINUTES=10  # More conservative sending
```

### Template Configuration

#### `TIERII_EMAIL_TEMPLATE_PATH`
- **Type**: String (file path)
- **Required**: No
- **Default**: `templates/email_template.html`
- **Description**: Path to HTML email template file
- **Validation**: File must exist and be readable

```bash
TIERII_EMAIL_TEMPLATE_PATH=templates/custom_template.html
```

### Testing Configuration

#### `TIERII_TEST_RECIPIENT_EMAIL`
- **Type**: String (email address)
- **Required**: No (Yes in test mode)
- **Description**: Email address for test sends
- **Use Case**: Verify campaigns before full deployment

```bash
TIERII_TEST_RECIPIENT_EMAIL=test@yourdomain.com
```

#### `TIERII_TEST_FALLBACK_FIRST_NAME`
- **Type**: String
- **Required**: No
- **Default**: `Friend`
- **Description**: Default first name when personalization fails
- **Use Case**: Graceful fallback for missing contact names

```bash
TIERII_TEST_FALLBACK_FIRST_NAME=Valued Customer
```

#### `TIERII_TEST_CSV_FILENAME`
- **Type**: String (file path)
- **Required**: No
- **Default**: `data/contacts/tier_i_tier_ii_emails_verified.csv`
- **Description**: Path to contact CSV file
- **Validation**: File must exist and be readable

```bash
TIERII_TEST_CSV_FILENAME=data/contacts/my_contacts.csv
```

## 📁 Configuration File Examples

### Production Configuration (`.env`)

```bash
# Production TierII Email Campaign Configuration
# Copy to .env and customize for your environment

# =============================================================================
# REQUIRED CONFIGURATION
# =============================================================================

# Sender email (must be from verified domain)
TIERII_SENDER_EMAIL=campaigns@yourdomain.com

# MailerSend API token (keep secure!)
TIERII_MAILERSEND_API_TOKEN=ms_token_your_production_token_here

# =============================================================================
# OPTIONAL CONFIGURATION
# =============================================================================

# Sender display name
TIERII_SENDER_NAME=Your Company Marketing Team

# Campaign batch processing
TIERII_CAMPAIGN_BATCH_SIZE=50
TIERII_CAMPAIGN_DELAY_MINUTES=5

# Email template
TIERII_EMAIL_TEMPLATE_PATH=templates/production_template.html

# Contact data
TIERII_TEST_CSV_FILENAME=data/contacts/production_contacts.csv

# Testing
TIERII_TEST_RECIPIENT_EMAIL=marketing-test@yourdomain.com
TIERII_TEST_FALLBACK_FIRST_NAME=Valued Partner
```

### Development Configuration (`.env.dev`)

```bash
# Development TierII Email Campaign Configuration

# Required
TIERII_SENDER_EMAIL=dev-test@yourdomain.com
TIERII_MAILERSEND_API_TOKEN=ms_token_your_dev_token_here

# Development-specific settings
TIERII_SENDER_NAME=Dev Team Testing
TIERII_CAMPAIGN_BATCH_SIZE=5          # Small batches for testing
TIERII_CAMPAIGN_DELAY_MINUTES=1       # Quick testing cycles
TIERII_TEST_RECIPIENT_EMAIL=developer@yourdomain.com
TIERII_TEST_CSV_FILENAME=data/test/testdata.csv
```

### Testing Configuration (`.env.test`)

```bash
# Test Environment Configuration

# Required (use test credentials)
TIERII_SENDER_EMAIL=test@example.com
TIERII_MAILERSEND_API_TOKEN=test_token_for_mocking

# Test-specific settings
TIERII_CAMPAIGN_BATCH_SIZE=1
TIERII_CAMPAIGN_DELAY_MINUTES=0
TIERII_TEST_RECIPIENT_EMAIL=test@example.com
TIERII_TEST_FALLBACK_FIRST_NAME=TestUser
TIERII_TEST_CSV_FILENAME=tests/fixtures/test_contacts.csv
```

## 🔍 Configuration Validation

### Automatic Validation

The system automatically validates configuration on startup:

```python
# Validation happens automatically
from src.config.settings import load_settings

try:
    settings = load_settings()
    print("✓ Configuration valid")
except ValidationError as e:
    print(f"❌ Configuration error: {e}")
```

### Validation Rules

| Field | Validation Rules |
|-------|------------------|
| `sender_email` | Valid email format, not empty |
| `mailersend_api_token` | Not empty, string type |
| `campaign_batch_size` | Integer, 1-100 range |
| `campaign_delay_minutes` | Integer, 1-60 range |
| `email_template_path` | File exists (if specified) |
| `test_csv_filename` | File exists (if specified) |

### Custom Validation

```python
from src.config.settings import TierIISettings
from pydantic import ValidationError

# Manual validation with custom data
try:
    settings = TierIISettings(
        sender_email="invalid-email",  # Will fail validation
        mailersend_api_token="test_token"
    )
except ValidationError as e:
    print(f"Validation errors: {e.errors()}")
```

## 🔒 Security Best Practices

### Environment Variable Security

```bash
# ✅ Good practices
export TIERII_MAILERSEND_API_TOKEN="$(cat /secure/path/token.txt)"
chmod 600 .env                    # Restrict file permissions
echo ".env" >> .gitignore        # Never commit secrets

# ❌ Bad practices  
TIERII_MAILERSEND_API_TOKEN=hardcoded_in_dockerfile  # Never do this
git add .env                     # Never commit .env files
```

### Production Security Checklist

- [ ] Use separate API tokens for dev/staging/production
- [ ] Rotate API tokens regularly (quarterly)
- [ ] Restrict `.env` file permissions (600/640)
- [ ] Use secret management systems in production
- [ ] Monitor API token usage and access
- [ ] Never log or display API tokens
- [ ] Use HTTPS for all webhook endpoints

## 🧪 Testing Configuration

### Test Mode Features

```python
# Enable test mode
settings = load_settings(test_mode=True)

# Test mode automatically:
# - Uses test-specific defaults
# - Enables additional validation
# - Provides mock-friendly settings
```

### Configuration Testing

```python
# Test configuration loading
def test_configuration():
    """Test that configuration loads correctly."""
    settings = load_settings(test_mode=True)
    
    assert settings.sender_email is not None
    assert settings.mailersend_api_token is not None
    assert 1 <= settings.campaign_batch_size <= 100
    assert 1 <= settings.campaign_delay_minutes <= 60
```

## 🚨 Troubleshooting

### Common Configuration Errors

#### Missing Required Variables
```bash
Error: Field required [type=missing, input=None]
Solution: Set TIERII_SENDER_EMAIL and TIERII_MAILERSEND_API_TOKEN
```

#### Invalid Email Format
```bash
Error: value is not a valid email address
Solution: Use proper email format (user@domain.com)
```

#### File Not Found
```bash
Error: Email template file not found
Solution: Check TIERII_EMAIL_TEMPLATE_PATH points to existing file
```

#### Invalid Range Values
```bash
Error: ensure this value is less than or equal to 100
Solution: Set TIERII_CAMPAIGN_BATCH_SIZE between 1-100
```

### Debug Configuration Loading

```python
# Debug configuration issues
import os
from src.config.settings import load_settings

# Check environment variables
print("Environment variables:")
for key in os.environ:
    if key.startswith('TIERII_'):
        print(f"  {key}={'*' * len(os.environ[key])}")  # Mask values

# Load with error details
try:
    settings = load_settings()
    print("✓ Configuration loaded successfully")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    print("Check your .env file and environment variables")
```

## 📚 Related Documentation

- **[MailerSend API Setup](mailersend.md)** - API token and domain setup
- **[Quick Start Guide](../quick-start.md)** - Basic configuration walkthrough  
- **[Security Practices](../compliance/security.md)** - Advanced security configuration
- **[Troubleshooting Guide](../guides/troubleshooting.md)** - Common configuration issues

---

**Configuration Version**: 0.1.0  
**Last Updated**: Current  
**Validation**: Pydantic 2.0+ with comprehensive error handling