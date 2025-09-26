# Troubleshooting Guide

Comprehensive troubleshooting documentation for the TierII Email Campaign system, covering common issues, diagnostic tools, and step-by-step solutions.

## 📋 Overview

This guide helps you diagnose and resolve common issues with the TierII Email Campaign system. It's organized by problem category with step-by-step solutions, diagnostic commands, and prevention strategies.

## 🚨 Quick Diagnostic Checklist

Before diving into specific issues, run this quick diagnostic checklist:

### 1. Environment Check
```bash
# Check Python version
python --version  # Should be 3.8+

# Check package installation
pip list | grep tierII

# Verify environment variables
python -c "import os; print('TIERII_SENDER_EMAIL:', os.getenv('TIERII_SENDER_EMAIL', 'NOT SET'))"
python -c "import os; print('TIERII_MAILERSEND_API_TOKEN:', os.getenv('TIERII_MAILERSEND_API_TOKEN', 'NOT SET'))"
```

### 2. Connection Test
```bash
# Test MailerSend API connection
python -m tierII_email_campaign.cli test-connection

# Test email validation
python -m tierII_email_campaign.cli validate-email your-email@example.com
```

### 3. Configuration Validation
```bash
# Validate configuration
python -m tierII_email_campaign.cli validate-config

# Check template syntax
python -m tierII_email_campaign.cli validate-template path/to/template.html
```

## 🔧 Configuration Issues

### Issue: Missing Environment Variables

**Symptoms:**
- `ConfigurationError: Missing required environment variable`
- `KeyError: 'TIERII_SENDER_EMAIL'`
- Application fails to start

**Diagnosis:**
```bash
# Check which variables are missing
python -c "
import os
required_vars = ['TIERII_SENDER_EMAIL', 'TIERII_MAILERSEND_API_TOKEN']
for var in required_vars:
    value = os.getenv(var)
    print(f'{var}: {\"SET\" if value else \"MISSING\"}')"
```

**Solutions:**

1. **Create .env file:**
```bash
# Create .env file in project root
cat > .env << EOF
TIERII_SENDER_EMAIL=your-email@yourdomain.com
TIERII_MAILERSEND_API_TOKEN=your-api-token-here
TIERII_BATCH_SIZE=50
TIERII_BATCH_DELAY=30
EOF
```

2. **Set environment variables (Windows):**
```cmd
set TIERII_SENDER_EMAIL=your-email@yourdomain.com
set TIERII_MAILERSEND_API_TOKEN=your-api-token-here
```

3. **Set environment variables (Linux/Mac):**
```bash
export TIERII_SENDER_EMAIL=your-email@yourdomain.com
export TIERII_MAILERSEND_API_TOKEN=your-api-token-here
```

**Prevention:**
- Use `.env.example` template
- Document required variables in README
- Add validation in application startup

### Issue: Invalid Configuration Values

**Symptoms:**
- `ValidationError: Invalid email format`
- `ValueError: Batch size must be positive`
- Configuration loads but validation fails

**Diagnosis:**
```python
# Validate configuration programmatically
from tierII_email_campaign.settings import Settings
from pydantic import ValidationError

try:
    settings = Settings()
    print("Configuration is valid")
    print(f"Sender email: {settings.sender_email}")
    print(f"Batch size: {settings.batch_size}")
except ValidationError as e:
    print("Configuration errors:")
    for error in e.errors():
        print(f"  {error['loc'][0]}: {error['msg']}")
```

**Solutions:**

1. **Fix email format:**
```bash
# Correct format
TIERII_SENDER_EMAIL=sender@yourdomain.com

# Incorrect formats to avoid
TIERII_SENDER_EMAIL=sender@domain  # Missing TLD
TIERII_SENDER_EMAIL=@domain.com    # Missing local part
```

2. **Fix numeric values:**
```bash
# Correct numeric values
TIERII_BATCH_SIZE=50        # Positive integer
TIERII_BATCH_DELAY=30       # Positive number
TIERII_MAX_RETRIES=3        # Non-negative integer

# Incorrect values to avoid
TIERII_BATCH_SIZE=-1        # Negative
TIERII_BATCH_DELAY=abc      # Non-numeric
```

3. **Fix boolean values:**
```bash
# Correct boolean values
TIERII_DEBUG=true
TIERII_ENABLE_LOGGING=false

# Incorrect values to avoid
TIERII_DEBUG=yes           # Use true/false
TIERII_ENABLE_LOGGING=1    # Use true/false
```

## 📧 Email Provider Issues

### Issue: MailerSend Authentication Failure

**Symptoms:**
- `AuthenticationError: Invalid API token`
- `HTTP 401 Unauthorized`
- `API token not found or invalid`

**Diagnosis:**
```bash
# Test API token directly
curl -X GET "https://api.mailersend.com/v1/domains" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json"

# Test with CLI tool
python -m tierII_email_campaign.cli test-connection --verbose
```

**Solutions:**

1. **Verify API token:**
   - Log into MailerSend dashboard
   - Go to Settings → API Tokens
   - Check token permissions and expiry
   - Generate new token if needed

2. **Update token in configuration:**
```bash
# Update .env file
TIERII_MAILERSEND_API_TOKEN=mlsn.your-new-token-here

# Or set environment variable
export TIERII_MAILERSEND_API_TOKEN=mlsn.your-new-token-here
```

3. **Check token format:**
```python
# Verify token format
import re

def validate_mailersend_token(token):
    # MailerSend tokens start with 'mlsn.'
    pattern = r'^mlsn\.[a-zA-Z0-9]{40,}$'
    return re.match(pattern, token) is not None

token = "your-token-here"
if validate_mailersend_token(token):
    print("Token format is valid")
else:
    print("Invalid token format")
```

**Prevention:**
- Store tokens securely
- Set token expiry reminders
- Use environment-specific tokens

### Issue: Domain Verification Problems

**Symptoms:**
- `Domain not verified` errors
- Emails not being sent
- `Sender domain not authorized`

**Diagnosis:**
```bash
# Check domain verification status
python -c "
from tierII_email_campaign.providers.mailersend import MailerSendProvider
provider = MailerSendProvider()
domains = provider.get_domains()
for domain in domains:
    print(f'Domain: {domain[\"name\"]}, Verified: {domain[\"domain_settings\"][\"send_paused\"] == False}')
"
```

**Solutions:**

1. **Verify domain in MailerSend:**
   - Go to MailerSend dashboard → Domains
   - Add your domain if not present
   - Complete DNS verification steps
   - Wait for verification (can take up to 48 hours)

2. **Check DNS records:**
```bash
# Check SPF record
nslookup -type=TXT yourdomain.com

# Check DKIM record
nslookup -type=TXT mailersend._domainkey.yourdomain.com

# Check DMARC record
nslookup -type=TXT _dmarc.yourdomain.com
```

3. **Use verified sender email:**
```bash
# Ensure sender email matches verified domain
TIERII_SENDER_EMAIL=noreply@yourdomain.com  # yourdomain.com must be verified
```

### Issue: Rate Limiting

**Symptoms:**
- `HTTP 429 Too Many Requests`
- `Rate limit exceeded`
- Emails sending slowly or failing

**Diagnosis:**
```python
# Check current rate limits
from tierII_email_campaign.providers.mailersend import MailerSendProvider

provider = MailerSendProvider()
try:
    result = provider.send_email(test_email)
    print("No rate limiting detected")
except Exception as e:
    if "429" in str(e) or "rate limit" in str(e).lower():
        print("Rate limiting detected")
        print(f"Error: {e}")
```

**Solutions:**

1. **Adjust batch settings:**
```bash
# Reduce batch size and increase delay
TIERII_BATCH_SIZE=10        # Smaller batches
TIERII_BATCH_DELAY=60       # Longer delay between batches
```

2. **Implement exponential backoff:**
```python
# Custom retry configuration
TIERII_MAX_RETRIES=5
TIERII_RETRY_DELAY=30
TIERII_RETRY_EXPONENTIAL_BASE=2
```

3. **Check MailerSend plan limits:**
   - Review your MailerSend plan
   - Check monthly/daily sending limits
   - Consider upgrading plan if needed

## 📄 CSV and Data Issues

### Issue: CSV File Not Found

**Symptoms:**
- `FileNotFoundError: No such file or directory`
- `CSV file not found at path`
- Application crashes on startup

**Diagnosis:**
```bash
# Check file existence and permissions
ls -la path/to/contacts.csv

# Check file format
file path/to/contacts.csv

# Preview file content
head -5 path/to/contacts.csv
```

**Solutions:**

1. **Verify file path:**
```python
# Check absolute vs relative paths
import os
from pathlib import Path

csv_path = "contacts.csv"
abs_path = Path(csv_path).absolute()
print(f"Looking for file at: {abs_path}")
print(f"File exists: {abs_path.exists()}")
print(f"Current directory: {os.getcwd()}")
```

2. **Use absolute paths:**
```bash
# Use full path to CSV file
python -m tierII_email_campaign.cli send-campaign \
  --contacts /full/path/to/contacts.csv \
  --template template.html
```

3. **Check file permissions:**
```bash
# Ensure file is readable
chmod 644 contacts.csv

# Check ownership
ls -la contacts.csv
```

### Issue: Invalid CSV Format

**Symptoms:**
- `CSV parsing error`
- `Missing required column: email`
- `Invalid CSV structure`

**Diagnosis:**
```python
# Validate CSV structure
import csv
import pandas as pd

def diagnose_csv(file_path):
    try:
        # Check if file can be read as CSV
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            print(f"Headers found: {headers}")
            
            # Check for required columns
            required_columns = ['email']
            missing = [col for col in required_columns if col not in headers]
            if missing:
                print(f"Missing required columns: {missing}")
            
            # Check first few rows
            for i, row in enumerate(reader):
                if i >= 3:  # Only check first 3 rows
                    break
                print(f"Row {i+2}: {row}")
                
    except Exception as e:
        print(f"CSV diagnosis error: {e}")

diagnose_csv("contacts.csv")
```

**Solutions:**

1. **Fix CSV headers:**
```csv
# Correct format
email,first_name,last_name,company
john@example.com,John,Doe,Acme Corp
jane@example.com,Jane,Smith,Beta LLC

# Common issues to avoid:
Email,First Name,Last Name  # Use lowercase, underscores
email;first_name;last_name  # Use commas, not semicolons
```

2. **Handle encoding issues:**
```python
# Check file encoding
import chardet

with open('contacts.csv', 'rb') as f:
    result = chardet.detect(f.read())
    print(f"Detected encoding: {result['encoding']}")

# Convert to UTF-8 if needed
import pandas as pd
df = pd.read_csv('contacts.csv', encoding='latin1')
df.to_csv('contacts_utf8.csv', encoding='utf-8', index=False)
```

3. **Clean CSV data:**
```python
# Remove empty rows and invalid emails
import pandas as pd

df = pd.read_csv('contacts.csv')
# Remove rows with empty emails
df = df.dropna(subset=['email'])
# Remove invalid email formats
df = df[df['email'].str.contains('@', na=False)]
# Save cleaned data
df.to_csv('contacts_cleaned.csv', index=False)
```

### Issue: Email Validation Failures

**Symptoms:**
- `Invalid email format` errors
- Emails skipped during processing
- High validation failure rate

**Diagnosis:**
```python
# Validate emails in CSV
import pandas as pd
import re

def validate_emails_in_csv(file_path):
    df = pd.read_csv(file_path)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    valid_emails = df['email'].str.match(email_pattern, na=False)
    invalid_count = (~valid_emails).sum()
    
    print(f"Total emails: {len(df)}")
    print(f"Valid emails: {valid_emails.sum()}")
    print(f"Invalid emails: {invalid_count}")
    
    if invalid_count > 0:
        print("\nInvalid emails:")
        invalid_emails = df[~valid_emails]['email'].tolist()
        for email in invalid_emails[:10]:  # Show first 10
            print(f"  {email}")

validate_emails_in_csv("contacts.csv")
```

**Solutions:**

1. **Clean email data:**
```python
# Email cleaning script
import pandas as pd
import re

def clean_emails(file_path):
    df = pd.read_csv(file_path)
    
    # Remove whitespace
    df['email'] = df['email'].str.strip()
    
    # Convert to lowercase
    df['email'] = df['email'].str.lower()
    
    # Remove invalid formats
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    df = df[df['email'].str.match(email_pattern, na=False)]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['email'])
    
    df.to_csv('contacts_cleaned.csv', index=False)
    print(f"Cleaned CSV saved with {len(df)} valid emails")

clean_emails("contacts.csv")
```

2. **Use email validation service:**
```python
# Enhanced email validation
from email_validator import validate_email, EmailNotValidError

def validate_email_enhanced(email):
    try:
        # Validate and get normalized result
        valid = validate_email(email)
        return True, valid.email
    except EmailNotValidError:
        return False, None

# Apply to CSV
df = pd.read_csv('contacts.csv')
validation_results = df['email'].apply(validate_email_enhanced)
df['email_valid'] = validation_results.apply(lambda x: x[0])
df['email_normalized'] = validation_results.apply(lambda x: x[1])

# Keep only valid emails
df_valid = df[df['email_valid']].copy()
df_valid['email'] = df_valid['email_normalized']
df_valid.drop(['email_valid', 'email_normalized'], axis=1, inplace=True)
```

## 🎨 Template Issues

### Issue: Template File Not Found

**Symptoms:**
- `Template file not found`
- `FileNotFoundError` when loading template
- Template rendering fails

**Diagnosis:**
```bash
# Check template file
ls -la path/to/template.html
file path/to/template.html

# Test template loading
python -c "
from pathlib import Path
template_path = 'template.html'
if Path(template_path).exists():
    print('Template file exists')
    with open(template_path) as f:
        content = f.read()
        print(f'Template size: {len(content)} characters')
else:
    print('Template file not found')
"
```

**Solutions:**

1. **Use absolute paths:**
```python
# Use absolute path for template
from pathlib import Path
template_path = Path(__file__).parent / "templates" / "email_template.html"
```

2. **Check template directory structure:**
```
project/
├── templates/
│   ├── email_template.html
│   └── welcome_template.html
├── contacts.csv
└── main.py
```

3. **Validate template content:**
```python
# Check template syntax
from jinja2 import Template, TemplateSyntaxError

def validate_template(template_path):
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Try to parse template
        template = Template(template_content)
        print("Template syntax is valid")
        return True
    except TemplateSyntaxError as e:
        print(f"Template syntax error: {e}")
        return False
    except Exception as e:
        print(f"Template validation error: {e}")
        return False

validate_template("template.html")
```

### Issue: Template Rendering Errors

**Symptoms:**
- `TemplateError: Variable not found`
- `UndefinedError` in template rendering
- Missing or incorrect variable substitution

**Diagnosis:**
```python
# Test template rendering with sample data
from jinja2 import Template

def test_template_rendering(template_path, sample_data):
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    template = Template(template_content)
    
    try:
        rendered = template.render(**sample_data)
        print("Template rendered successfully")
        print(f"Rendered length: {len(rendered)} characters")
        return rendered
    except Exception as e:
        print(f"Template rendering error: {e}")
        return None

# Test with sample data
sample_data = {
    'first_name': 'John',
    'last_name': 'Doe',
    'company': 'Acme Corp',
    'email': 'john@example.com'
}

test_template_rendering("template.html", sample_data)
```

**Solutions:**

1. **Fix undefined variables:**
```html
<!-- Use default values for optional variables -->
<h1>Hello {{first_name|default('Friend')}}!</h1>
<p>Company: {{company|default('N/A')}}</p>

<!-- Check if variable exists -->
{% if company %}
<p>Your company: {{company}}</p>
{% endif %}
```

2. **Validate required variables:**
```python
# Check template variables against CSV columns
import re
from jinja2 import Template

def find_template_variables(template_path):
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Find all {{variable}} patterns
    variables = re.findall(r'\{\{\s*(\w+)', content)
    return list(set(variables))

def validate_template_data_match(template_path, csv_path):
    import pandas as pd
    
    template_vars = find_template_variables(template_path)
    df = pd.read_csv(csv_path)
    csv_columns = df.columns.tolist()
    
    missing_vars = [var for var in template_vars if var not in csv_columns]
    
    if missing_vars:
        print(f"Missing CSV columns for template variables: {missing_vars}")
        return False
    else:
        print("All template variables have corresponding CSV columns")
        return True

validate_template_data_match("template.html", "contacts.csv")
```

3. **Create robust templates:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{subject|default('Email Campaign')}}</title>
</head>
<body>
    <h1>Hello {{first_name|default('Friend')}}!</h1>
    
    {% if last_name %}
    <p>Full name: {{first_name}} {{last_name}}</p>
    {% endif %}
    
    {% if company %}
    <p>We hope things are going well at {{company}}.</p>
    {% endif %}
    
    <p>Best regards,<br>
    {{sender_name|default('The Team')}}</p>
</body>
</html>
```

## 🔄 Campaign Execution Issues

### Issue: Campaign Fails to Start

**Symptoms:**
- Campaign initialization errors
- `No contacts loaded` messages
- Process exits immediately

**Diagnosis:**
```python
# Debug campaign initialization
from tierII_email_campaign.email_campaign import EmailCampaign
from tierII_email_campaign.settings import Settings

def debug_campaign_initialization():
    try:
        # Test settings loading
        settings = Settings()
        print(f"Settings loaded: {settings.sender_email}")
        
        # Test campaign creation
        campaign = EmailCampaign(
            csv_file="contacts.csv",
            batch_size=settings.batch_size,
            batch_delay=settings.batch_delay
        )
        print("Campaign created successfully")
        
        # Test contact loading
        contacts = campaign.load_contacts()
        print(f"Contacts loaded: {len(contacts)}")
        
        return True
    except Exception as e:
        print(f"Campaign initialization error: {e}")
        return False

debug_campaign_initialization()
```

**Solutions:**

1. **Check all prerequisites:**
```bash
# Verify all required files exist
ls -la contacts.csv template.html

# Check environment variables
env | grep TIERII

# Test configuration
python -m tierII_email_campaign.cli validate-config
```

2. **Use step-by-step debugging:**
```python
# Debug each step individually
import sys
from tierII_email_campaign.csv_reader import load_contacts
from tierII_email_campaign.template_engine import TemplateEngine

# Step 1: Load contacts
try:
    contacts = load_contacts("contacts.csv")
    print(f"✓ Loaded {len(contacts)} contacts")
except Exception as e:
    print(f"✗ Contact loading failed: {e}")
    sys.exit(1)

# Step 2: Load template
try:
    engine = TemplateEngine()
    template = engine.load_template("template.html")
    print("✓ Template loaded successfully")
except Exception as e:
    print(f"✗ Template loading failed: {e}")
    sys.exit(1)

# Step 3: Test rendering
try:
    rendered = engine.render(template, contacts[0])
    print("✓ Template rendering successful")
except Exception as e:
    print(f"✗ Template rendering failed: {e}")
    sys.exit(1)
```

### Issue: Partial Campaign Failures

**Symptoms:**
- Some emails send, others fail
- Inconsistent success rates
- Mixed error messages

**Diagnosis:**
```python
# Analyze campaign results
def analyze_campaign_results(result):
    print(f"Campaign Results:")
    print(f"  Total contacts: {result['total_contacts']}")
    print(f"  Successful sends: {result['successful_sends']}")
    print(f"  Failed sends: {result['failed_sends']}")
    success_rate = result['successful_sends'] / result['total_contacts'] if result['total_contacts'] > 0 else 0
    print(f"  Success rate: {success_rate*100:.1f}%")
    
    if result.get('errors'):
        print(f"\nError breakdown:")
        error_counts = {}
        for error in result['errors']:
            error_type = error.get('type', 'Unknown')
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in error_counts.items():
            print(f"  {error_type}: {count}")
```

**Solutions:**

1. **Implement robust error handling:**
```python
# Enhanced error handling in campaign
class RobustEmailCampaign(EmailCampaign):
    def send_email_with_retry(self, contact, template, max_retries=3):
        for attempt in range(max_retries):
            try:
                result = self.provider.send_email(contact, template)
                if result.get('success'):
                    return result
                else:
                    # Log the error but continue
                    self.logger.warning(f"Send failed (attempt {attempt+1}): {result.get('error')}")
            except Exception as e:
                self.logger.error(f"Send exception (attempt {attempt+1}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return {'success': False, 'error': 'Max retries exceeded'}
```

2. **Add detailed logging:**
```python
# Configure detailed logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('campaign.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('tierII_email_campaign')
```

3. **Implement progress tracking:**
```python
# Progress tracking for long campaigns
from tqdm import tqdm

def send_campaign_with_progress(self, contacts, template):
    results = []
    
    with tqdm(total=len(contacts), desc="Sending emails") as pbar:
        for i, contact in enumerate(contacts):
            try:
                result = self.send_email(contact, template)
                results.append(result)
                
                # Update progress
                pbar.set_postfix({
                    'Success': sum(1 for r in results if r.get('success')),
                    'Failed': sum(1 for r in results if not r.get('success'))
                })
                pbar.update(1)
                
            except Exception as e:
                self.logger.error(f"Failed to send to {contact['email']}: {e}")
                results.append({'success': False, 'error': str(e)})
                pbar.update(1)
    
    return results
```

## 🔍 Performance Issues

### Issue: Slow Campaign Execution

**Symptoms:**
- Campaigns take much longer than expected
- High memory usage
- System becomes unresponsive

**Diagnosis:**
```python
# Profile campaign performance
import cProfile
import pstats
from tierII_email_campaign.email_campaign import EmailCampaign

def profile_campaign():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run campaign
    campaign = EmailCampaign("contacts.csv")
    campaign.send_campaign("template.html")
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions

profile_campaign()
```

**Solutions:**

1. **Optimize batch processing:**
```python
# Efficient batch processing
class OptimizedEmailCampaign(EmailCampaign):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = min(self.batch_size, 100)  # Cap batch size
        self.batch_delay = max(self.batch_delay, 1)   # Minimum delay
    
    def process_batch(self, batch):
        # Process batch with connection pooling
        with self.provider.get_connection_pool() as pool:
            results = []
            for contact in batch:
                result = self.send_email_pooled(contact, pool)
                results.append(result)
            return results
```

2. **Implement memory optimization:**
```python
# Memory-efficient contact processing
def process_contacts_streaming(csv_file, batch_size=50):
    """Process contacts in streaming fashion to reduce memory usage."""
    import pandas as pd
    
    # Read CSV in chunks
    chunk_iter = pd.read_csv(csv_file, chunksize=batch_size)
    
    for chunk in chunk_iter:
        contacts = chunk.to_dict('records')
        yield contacts
        
        # Force garbage collection
        import gc
        gc.collect()

# Usage
for contact_batch in process_contacts_streaming("large_contacts.csv"):
    process_batch(contact_batch)
```

3. **Add performance monitoring:**
```python
# Performance monitoring
import time
import psutil
import os

class PerformanceMonitor:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss
    
    def get_stats(self):
        current_time = time.time()
        current_memory = self.process.memory_info().rss
        
        return {
            'elapsed_time': current_time - self.start_time,
            'memory_usage_mb': current_memory / 1024 / 1024,
            'memory_increase_mb': (current_memory - self.start_memory) / 1024 / 1024,
            'cpu_percent': self.process.cpu_percent()
        }

# Usage in campaign
monitor = PerformanceMonitor()
# ... run campaign ...
stats = monitor.get_stats()
print(f"Campaign completed in {stats['elapsed_time']:.2f}s")
print(f"Memory usage: {stats['memory_usage_mb']:.1f}MB")
```

## 🛠️ Diagnostic Tools

### Built-in CLI Diagnostics

```bash
# Test all connections
python -m tierII_email_campaign.cli diagnose

# Test specific components
python -m tierII_email_campaign.cli test-connection
python -m tierII_email_campaign.cli validate-config
python -m tierII_email_campaign.cli validate-template template.html
python -m tierII_email_campaign.cli validate-csv contacts.csv

# Get system information
python -m tierII_email_campaign.cli system-info
```

### Custom Diagnostic Script

```python
#!/usr/bin/env python3
# diagnostic_tool.py - Comprehensive system diagnostic

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def run_diagnostics():
    """Run comprehensive system diagnostics."""
    results = {
        'timestamp': datetime.now().isoformat(),
        'system': {},
        'environment': {},
        'configuration': {},
        'connectivity': {},
        'files': {}
    }
    
    # System information
    import platform
    results['system'] = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'architecture': platform.architecture(),
        'processor': platform.processor()
    }
    
    # Environment variables
    tierii_vars = {k: v for k, v in os.environ.items() if k.startswith('TIERII_')}
    results['environment'] = {
        'tierii_variables': len(tierii_vars),
        'variables': {k: 'SET' if v else 'EMPTY' for k, v in tierii_vars.items()}
    }
    
    # Configuration validation
    try:
        from tierII_email_campaign.settings import Settings
        settings = Settings()
        results['configuration'] = {
            'status': 'VALID',
            'sender_email': settings.sender_email,
            'batch_size': settings.batch_size,
            'batch_delay': settings.batch_delay
        }
    except Exception as e:
        results['configuration'] = {
            'status': 'INVALID',
            'error': str(e)
        }
    
    # Connectivity test
    try:
        from tierII_email_campaign.providers.mailersend import MailerSendProvider
        provider = MailerSendProvider()
        connected = provider.test_connection()
        results['connectivity'] = {
            'mailersend': 'CONNECTED' if connected else 'FAILED'
        }
    except Exception as e:
        results['connectivity'] = {
            'mailersend': 'ERROR',
            'error': str(e)
        }
    
    # File checks
    common_files = ['contacts.csv', 'template.html', '.env']
    for file_name in common_files:
        file_path = Path(file_name)
        results['files'][file_name] = {
            'exists': file_path.exists(),
            'size': file_path.stat().st_size if file_path.exists() else 0,
            'readable': os.access(file_path, os.R_OK) if file_path.exists() else False
        }
    
    return results

def print_diagnostic_report(results):
    """Print formatted diagnostic report."""
    print("=" * 60)
    print("TierII Email Campaign System Diagnostics")
    print("=" * 60)
    
    print(f"\n📊 System Information:")
    print(f"  Python Version: {results['system']['python_version'].split()[0]}")
    print(f"  Platform: {results['system']['platform']}")
    
    print(f"\n🔧 Environment:")
    env_vars = results['environment']['variables']
    for var, status in env_vars.items():
        status_icon = "✓" if status == "SET" else "✗"
        print(f"  {status_icon} {var}: {status}")
    
    print(f"\n⚙️  Configuration:")
    config = results['configuration']
    if config['status'] == 'VALID':
        print(f"  ✓ Configuration: VALID")
        print(f"  ✓ Sender Email: {config['sender_email']}")
        print(f"  ✓ Batch Size: {config['batch_size']}")
    else:
        print(f"  ✗ Configuration: INVALID")
        print(f"    Error: {config['error']}")
    
    print(f"\n🌐 Connectivity:")
    connectivity = results['connectivity']
    for service, status in connectivity.items():
        if service != 'error':
            status_icon = "✓" if status == "CONNECTED" else "✗"
            print(f"  {status_icon} {service.title()}: {status}")
    
    print(f"\n📁 Files:")
    files = results['files']
    for file_name, info in files.items():
        exists_icon = "✓" if info['exists'] else "✗"
        print(f"  {exists_icon} {file_name}: {'EXISTS' if info['exists'] else 'MISSING'}")
        if info['exists']:
            print(f"    Size: {info['size']} bytes, Readable: {info['readable']}")

if __name__ == "__main__":
    try:
        results = run_diagnostics()
        print_diagnostic_report(results)
        
        # Save detailed results to file
        with open('diagnostic_report.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: diagnostic_report.json")
        
    except Exception as e:
        print(f"Diagnostic tool error: {e}")
        sys.exit(1)
```

## 📞 Getting Help

### Log Analysis

```bash
# Enable debug logging
export TIERII_LOG_LEVEL=DEBUG

# Run campaign with detailed logging
python -m tierII_email_campaign.cli send-campaign \
  --contacts contacts.csv \
  --template template.html \
  --log-file campaign.log

# Analyze logs
grep ERROR campaign.log
grep WARNING campaign.log
tail -f campaign.log  # Monitor real-time
```

### Community Resources

1. **GitHub Issues**: Report bugs and request features
2. **Documentation**: Check latest documentation updates
3. **Stack Overflow**: Search for similar issues with tag `tierII-email-campaign`

### Creating Bug Reports

When reporting issues, include:

1. **System Information:**
```bash
python --version
pip list | grep tierII
python -m tierII_email_campaign.cli system-info
```

2. **Configuration (sanitized):**
```bash
# Remove sensitive data before sharing
env | grep TIERII | sed 's/=.*/=***REDACTED***/'
```

3. **Error Messages:**
   - Full error traceback
   - Log file excerpts
   - Steps to reproduce

4. **Sample Data:**
   - Anonymized CSV sample
   - Template file (if relevant)
   - Configuration file (sanitized)

### Emergency Recovery

If the system is completely broken:

1. **Reset configuration:**
```bash
# Backup current config
cp .env .env.backup

# Create minimal working config
cat > .env << EOF
TIERII_SENDER_EMAIL=test@yourdomain.com
TIERII_MAILERSEND_API_TOKEN=your-token-here
TIERII_BATCH_SIZE=1
TIERII_BATCH_DELAY=5
EOF
```

2. **Test with minimal data:**
```bash
# Create test CSV with one contact
echo "email,first_name" > test_contacts.csv
echo "test@example.com,Test" >> test_contacts.csv

# Create minimal template
echo "<h1>Hello {{first_name}}!</h1>" > test_template.html

# Test campaign
python -m tierII_email_campaign.cli send-campaign \
  --contacts test_contacts.csv \
  --template test_template.html \
  --dry-run
```

3. **Reinstall package:**
```bash
pip uninstall tierII-email-campaign
pip install tierII-email-campaign --force-reinstall
```

## 📚 Related Documentation

- **[Quick Start Guide](../quick-start.md)** - Initial setup and configuration
- **[Configuration Reference](../api/configuration.md)** - Complete configuration options
- **[Development Guide](development.md)** - Development and testing procedures
- **[API Documentation](../api/)** - Complete API reference

---

**Troubleshooting Guide Version**: 0.1.0  
**Last Updated**: 2024  
**Support Level**: Community-driven with comprehensive self-service resources