# Campaign Management Guide

Complete guide for creating, configuring, and managing email campaigns with the TierII Email Campaign system.

## 📋 Overview

This guide covers everything you need to know about managing email campaigns, from initial setup to monitoring and optimization. Whether you're running your first campaign or optimizing existing ones, this guide provides practical steps and best practices.

## 🚀 Quick Campaign Setup

### 1. Basic Campaign Structure

```bash
# Typical campaign workflow
1. Prepare contact data (CSV)
2. Configure campaign settings
3. Set up email templates
4. Test with small batch
5. Run full campaign
6. Monitor and analyze results
```

### 2. Minimum Required Setup

```bash
# Environment variables (required)
export TIERII_SENDER_EMAIL="your-email@yourdomain.com"
export TIERII_MAILERSEND_API_TOKEN="your-api-token"

# Basic campaign execution
python -m tierII_email_campaign
```

## 📊 Contact Data Management

### CSV File Format Requirements

#### Required Fields
```csv
email,first_name,last_name
john.doe@example.com,John,Doe
jane.smith@example.com,Jane,Smith
```

#### Extended Format (Recommended)
```csv
email,first_name,last_name,company,position,industry,location,custom_field_1,custom_field_2
john.doe@example.com,John,Doe,Acme Corp,Manager,Technology,New York,Premium,Q4-2024
jane.smith@example.com,Jane,Smith,Beta LLC,Director,Healthcare,California,Standard,Q1-2025
```

#### Supported Optional Fields
- `company`: Company name
- `position`: Job title/position
- `industry`: Industry sector
- `location`: Geographic location
- `phone`: Phone number
- `website`: Company website
- `custom_field_*`: Any custom fields for personalization

### Data Validation Rules

```python
# Email validation
- Must be valid email format (RFC 5322 compliant)
- Must not be empty or null
- Duplicates are automatically removed
- Invalid emails are logged and skipped

# Name validation
- first_name and last_name are recommended but not required
- Empty names default to "Valued Customer" in templates
- Names are automatically capitalized

# Custom field validation
- All custom fields are optional
- Values are sanitized for template safety
- Long values (>500 chars) are truncated with warning
```

### Contact Data Preparation

#### 1. Data Cleaning Checklist

```bash
✅ Remove duplicate email addresses
✅ Validate email format
✅ Standardize name formatting (Title Case)
✅ Clean company names (remove extra spaces, standardize)
✅ Validate phone numbers (if included)
✅ Check for required fields
✅ Remove test/invalid emails
✅ Ensure UTF-8 encoding
```

#### 2. Data Quality Script

```python
# Use the built-in data validation
from tierII_email_campaign.csv_reader import validate_contact_data

# Validate your CSV before campaign
contacts = validate_contact_data("path/to/your/contacts.csv")
print(f"Valid contacts: {len(contacts)}")

# Check for common issues
issues = check_data_quality(contacts)
for issue in issues:
    print(f"Warning: {issue}")
```

#### 3. Contact Segmentation

```python
# Example: Segment contacts by industry
def segment_contacts_by_industry(csv_path: str) -> Dict[str, str]:
    """Create separate CSV files for each industry."""
    
    contacts = load_contacts(csv_path)
    segments = {}
    
    for contact in contacts:
        industry = contact.get('industry', 'general')
        if industry not in segments:
            segments[industry] = []
        segments[industry].append(contact)
    
    # Save segments to separate files
    for industry, industry_contacts in segments.items():
        segment_file = f"contacts_{industry.lower().replace(' ', '_')}.csv"
        save_contacts_to_csv(industry_contacts, segment_file)
        segments[industry] = segment_file
    
    return segments
```

## 📧 Email Template System

### Template Structure

#### Basic Template Format
```html
<!-- templates/basic_campaign.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{subject}}</title>
</head>
<body>
    <h1>Hello {{first_name}}!</h1>
    
    <p>We're excited to share this update with you.</p>
    
    <p>Best regards,<br>
    The {{company_name}} Team</p>
    
    <p><small>
        <a href="{{unsubscribe_url}}">Unsubscribe</a> | 
        <a href="{{preferences_url}}">Update Preferences</a>
    </small></p>
</body>
</html>
```

#### Advanced Template with Conditionals
```html
<!-- templates/personalized_campaign.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{subject}}</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background-color: #f8f9fa; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background-color: #e9ecef; padding: 15px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Hello {{first_name|default:"Valued Customer"}}!</h1>
        </div>
        
        <div class="content">
            {% if company %}
            <p>We hope things are going well at {{company}}.</p>
            {% endif %}
            
            {% if position %}
            <p>As a {{position}}, you might be interested in our latest updates.</p>
            {% endif %}
            
            <p>{{main_message}}</p>
            
            {% if industry == "cannabis" %}
            <p><strong>Cannabis Industry Update:</strong> {{cannabis_specific_content}}</p>
            {% endif %}
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{cta_url}}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                    {{cta_text|default:"Learn More"}}
                </a>
            </div>
        </div>
        
        <div class="footer">
            <p>{{company_name}} | {{company_address}}</p>
            <p>
                <a href="{{unsubscribe_url}}">Unsubscribe</a> | 
                <a href="{{preferences_url}}">Update Preferences</a> |
                <a href="{{view_online_url}}">View Online</a>
            </p>
        </div>
    </div>
</body>
</html>
```

### Available Template Variables

#### Contact Variables
```python
# Automatically available from contact data
{{email}}           # Contact's email address
{{first_name}}      # First name
{{last_name}}       # Last name
{{full_name}}       # "First Last" (auto-generated)
{{company}}         # Company name
{{position}}        # Job position
{{industry}}        # Industry sector
{{location}}        # Geographic location
{{phone}}           # Phone number
{{website}}         # Website URL

# Custom fields (from CSV)
{{custom_field_1}}  # Any custom field from CSV
{{custom_field_2}}  # Additional custom fields
```

#### System Variables
```python
# Automatically generated
{{campaign_date}}     # Current date (YYYY-MM-DD)
{{campaign_time}}     # Current time (HH:MM:SS)
{{unsubscribe_url}}   # Auto-generated unsubscribe link
{{preferences_url}}   # Preference management link
{{view_online_url}}   # View email online link

# Configuration variables
{{company_name}}      # From TIERII_COMPANY_NAME
{{company_address}}   # From TIERII_COMPANY_ADDRESS
{{sender_name}}       # From TIERII_SENDER_NAME
{{sender_email}}      # From TIERII_SENDER_EMAIL
```

#### Global Campaign Variables
```python
# Set via environment or configuration
{{campaign_name}}     # Campaign identifier
{{campaign_type}}     # Campaign category
{{special_offer}}     # Promotional content
{{deadline_date}}     # Campaign deadline
{{discount_code}}     # Promotional code
```

### Template Functions

#### Built-in Functions
```html
<!-- Date formatting -->
{{campaign_date|format_date:"%B %d, %Y"}}  <!-- January 15, 2024 -->

<!-- Text formatting -->
{{first_name|capitalize}}                   <!-- John -->
{{company|upper}}                          <!-- ACME CORP -->
{{message|truncate:100}}                   <!-- Truncate to 100 chars -->

<!-- Conditional display -->
{{company|default:"Your Company"}}         <!-- Default if empty -->

<!-- URL encoding -->
{{custom_url|urlencode}}                   <!-- URL-safe encoding -->

<!-- Currency formatting -->
{{price|format_currency}}                  <!-- $1,234.56 -->
```

#### Custom Template Functions
```python
# Add custom functions in template configuration
TEMPLATE_FUNCTIONS = {
    'format_phone': lambda phone: f"({phone[:3]}) {phone[3:6]}-{phone[6:]}" if phone else "",
    'business_greeting': lambda position: f"Dear {position}" if position else "Dear Professional",
    'industry_specific': lambda industry: INDUSTRY_MESSAGES.get(industry, DEFAULT_MESSAGE)
}
```

### Template Testing

#### 1. Template Validation
```python
# Validate template syntax before campaign
from tierII_email_campaign.template_engine import validate_template

try:
    validate_template("templates/my_campaign.html")
    print("✅ Template syntax is valid")
except TemplateError as e:
    print(f"❌ Template error: {e}")
```

#### 2. Preview Generation
```python
# Generate preview with sample data
sample_contact = {
    'email': 'john.doe@example.com',
    'first_name': 'John',
    'last_name': 'Doe',
    'company': 'Acme Corp',
    'position': 'Manager'
}

preview = generate_template_preview("templates/my_campaign.html", sample_contact)
print(preview.html_content)
```

#### 3. A/B Testing Templates
```python
# Test multiple template versions
templates = [
    "templates/version_a.html",
    "templates/version_b.html"
]

# Split contacts for A/B testing
contacts_a, contacts_b = split_contacts_for_ab_test(contacts, 0.5)

# Run campaigns with different templates
campaign_a = run_campaign(contacts_a, templates[0])
campaign_b = run_campaign(contacts_b, templates[1])

# Compare results
compare_campaign_results(campaign_a, campaign_b)
```

## ⚙️ Campaign Configuration

### Basic Configuration

#### Environment Variables
```bash
# Core settings
export TIERII_SENDER_EMAIL="campaigns@yourdomain.com"
export TIERII_SENDER_NAME="Your Company Name"
export TIERII_MAILERSEND_API_TOKEN="your-api-token"

# Campaign settings
export TIERII_BATCH_SIZE="50"              # Emails per batch
export TIERII_BATCH_DELAY="30"             # Seconds between batches
export TIERII_MAX_RETRIES="3"              # Retry failed emails
export TIERII_TEST_MODE="false"            # Set to true for testing

# Template settings
export TIERII_TEMPLATE_PATH="templates/default.html"
export TIERII_SUBJECT_LINE="Your Campaign Subject"
```

#### Configuration File (.env)
```bash
# .env file for project-specific settings
TIERII_SENDER_EMAIL=campaigns@yourdomain.com
TIERII_SENDER_NAME=Your Company Name
TIERII_MAILERSEND_API_TOKEN=your-api-token

# Campaign configuration
TIERII_BATCH_SIZE=50
TIERII_BATCH_DELAY=30
TIERII_MAX_RETRIES=3
TIERII_TEST_MODE=false

# Template configuration
TIERII_TEMPLATE_PATH=templates/campaign.html
TIERII_SUBJECT_LINE=Important Update from {{company_name}}

# Global template variables
TIERII_COMPANY_NAME=Your Company Name
TIERII_COMPANY_ADDRESS=123 Main St, City, State 12345
TIERII_CAMPAIGN_NAME=Q1 2024 Newsletter
```

### Advanced Configuration

#### Campaign-Specific Settings
```python
# campaign_config.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Campaign configuration is handled through EmailCampaign initialization
# and environment variables. No separate CampaignConfig class is needed.

def create_campaign_config(
    name: str,
    description: str,
    template_path: str,
    subject_line: str,
    batch_size: int = 50,
    batch_delay: int = 30,  # seconds
    max_retries: int = 3,
    retry_delay: int = 300,  # 5 minutes
    emails_per_hour: Optional[int] = None,
    emails_per_day: Optional[int] = None,
    global_variables: Dict[str, Any] = None,
    track_opens: bool = True,
    track_clicks: bool = True,
    track_unsubscribes: bool = True,
    test_mode: bool = False,
    test_email_override: Optional[str] = None
) -> Dict[str, Any]:
    """Create campaign configuration dictionary."""
    
    config = {
        'name': name,
        'description': description,
        'template_path': template_path,
        'subject_line': subject_line,
        'batch_size': batch_size,
        'batch_delay': batch_delay,
        'max_retries': max_retries,
        'retry_delay': retry_delay,
        'emails_per_hour': emails_per_hour,
        'emails_per_day': emails_per_day,
        'global_variables': global_variables or {},
        'track_opens': track_opens,
        'track_clicks': track_clicks,
        'track_unsubscribes': track_unsubscribes,
        'test_mode': test_mode,
        'test_email_override': test_email_override
    }
    
    return config
```

#### Batch Processing Strategies

```python
# Different batch processing approaches
BATCH_STRATEGIES = {
    'conservative': {
        'batch_size': 25,
        'batch_delay': 60,
        'emails_per_hour': 500
    },
    'standard': {
        'batch_size': 50,
        'batch_delay': 30,
        'emails_per_hour': 1000
    },
    'aggressive': {
        'batch_size': 100,
        'batch_delay': 15,
        'emails_per_hour': 2000
    }
}

# Select strategy based on list size
def select_batch_strategy(contact_count: int) -> Dict[str, Any]:
    if contact_count < 500:
        return BATCH_STRATEGIES['aggressive']
    elif contact_count < 2000:
        return BATCH_STRATEGIES['standard']
    else:
        return BATCH_STRATEGIES['conservative']
```

## 🚀 Running Campaigns

### Command Line Interface

#### Basic Campaign Execution
```bash
# Run with default settings
python -m tierII_email_campaign

# Specify custom CSV file
python -m tierII_email_campaign --contacts contacts/my_list.csv

# Use custom template
python -m tierII_email_campaign --template templates/special_offer.html

# Test mode (sends to test email only)
python -m tierII_email_campaign --test-mode --test-email your-test@email.com

# Dry run (validate without sending)
python -m tierII_email_campaign --dry-run
```

#### Advanced CLI Options
```bash
# Full command with all options
python -m tierII_email_campaign \
    --contacts contacts/q1_newsletter.csv \
    --template templates/newsletter.html \
    --subject "Q1 2024 Newsletter - Important Updates" \
    --batch-size 25 \
    --batch-delay 45 \
    --max-retries 2 \
    --sender-name "Marketing Team" \
    --campaign-name "Q1-Newsletter-2024" \
    --verbose
```

### Programmatic Campaign Execution

#### Basic Python Script
```python
#!/usr/bin/env python3
"""
Basic campaign execution script.
"""

from tierII_email_campaign import EmailCampaign
from tierII_email_campaign.settings import Settings

def run_basic_campaign():
    """Run a basic email campaign."""
    
    # Load configuration
    settings = Settings()
    
    # Initialize campaign
    campaign = EmailCampaign(
        csv_file="contacts/newsletter_list.csv",
        template_path="templates/newsletter.html",
        batch_size=settings.batch_size,
        batch_delay=settings.batch_delay
    )
    
    # Run campaign
    results = campaign.send_campaign()
    
    # Print results
    print(f"Campaign completed!")
    print(f"Successful sends: {results.successful_sends}")
    print(f"Failed sends: {results.failed_sends}")
    print(f"Total contacts: {results.total_contacts}")

if __name__ == "__main__":
    run_basic_campaign()
```

#### Advanced Campaign Script
```python
#!/usr/bin/env python3
"""
Advanced campaign with custom configuration and error handling.
"""

import logging
from datetime import datetime
from pathlib import Path
from tierII_email_campaign import EmailCampaign

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'campaign_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

def run_advanced_campaign():
    """Run an advanced email campaign with full configuration."""
    
    # Campaign configuration using dictionary
    config = create_campaign_config(
        name="Q1_2024_Newsletter",
        description="Quarterly newsletter with industry updates",
        template_path="templates/newsletter_q1_2024.html",
        subject_line="Q1 2024 Updates - {{company_name}}",
        
        # Batch settings
        batch_size=50,
        batch_delay=30,
        max_retries=3,
        
        # Rate limiting
        emails_per_hour=1000,
        
        # Global variables
        global_variables={
            'campaign_name': 'Q1 2024 Newsletter',
            'special_offer': '20% off all services',
            'deadline_date': '2024-03-31',
            'cta_url': 'https://yoursite.com/q1-offer',
            'cta_text': 'Claim Your Discount'
        },
        
        # Tracking
        track_opens=True,
        track_clicks=True
    )
    
    try:
        # Initialize campaign with CSV file
        campaign = EmailCampaign(
            csv_file="contacts/q1_newsletter_list.csv",
            batch_size=config['batch_size'],
            delay_minutes=config['batch_delay'] / 60
        )
        
        # Load and validate contacts
        contacts = campaign.load_contacts()
        logging.info(f"Loaded {len(contacts)} contacts")
        
        # Run campaign
        logging.info("Starting campaign execution...")
        results = campaign.send_campaign()
        
        # Log results
        logging.info(f"Campaign completed successfully!")
        logging.info(f"Total contacts: {results['total_contacts']}")
        logging.info(f"Successful sends: {results['successful_sends']}")
        logging.info(f"Failed sends: {results['failed_sends']}")
        success_rate = results['successful_sends'] / results['total_contacts'] if results['total_contacts'] > 0 else 0
        logging.info(f"Success rate: {success_rate:.2%}")
        
        # Save campaign results
        results_file = f"campaign_results_{config['name']}.json"
        with open(results_file, 'w') as f:
            import json
            json.dump(results, f, indent=2, default=str)
        logging.info(f"Results saved to: {results_file}")
        
    except Exception as e:
        logging.error(f"Campaign failed: {str(e)}")
        raise
        
    except Exception as e:
        logging.error(f"Campaign failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_advanced_campaign()
```

### Scheduled Campaigns

#### Using Cron (Linux/Mac)
```bash
# Add to crontab (crontab -e)

# Daily newsletter at 9 AM
0 9 * * * cd /path/to/tierII_emails && python -m tierII_email_campaign --contacts daily_list.csv

# Weekly newsletter every Monday at 10 AM
0 10 * * 1 cd /path/to/tierII_emails && python weekly_campaign.py

# Monthly report on first day of month at 8 AM
0 8 1 * * cd /path/to/tierII_emails && python monthly_report.py
```

#### Using Windows Task Scheduler
```batch
REM Create batch file for Windows Task Scheduler
@echo off
cd /d "C:\path\to\tierII_emails"
python -m tierII_email_campaign --contacts weekly_list.csv
```

#### Using Python Scheduler
```python
import schedule
import time
from datetime import datetime

def run_daily_campaign():
    """Run daily campaign."""
    logging.info(f"Starting daily campaign at {datetime.now()}")
    # Your campaign code here
    
def run_weekly_campaign():
    """Run weekly campaign."""
    logging.info(f"Starting weekly campaign at {datetime.now()}")
    # Your campaign code here

# Schedule campaigns
schedule.every().day.at("09:00").do(run_daily_campaign)
schedule.every().monday.at("10:00").do(run_weekly_campaign)

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
```

## 📊 Campaign Monitoring

### Real-time Monitoring

#### Progress Tracking
```python
from tierII_email_campaign.monitoring import CampaignMonitor

def monitor_campaign_progress(campaign_id: str):
    """Monitor campaign progress in real-time."""
    
    monitor = CampaignMonitor(campaign_id)
    
    while not monitor.is_complete():
        status = monitor.get_status()
        
        print(f"\rProgress: {status.progress:.1%} | "
              f"Sent: {status.sent} | "
              f"Failed: {status.failed} | "
              f"Rate: {status.send_rate:.1f}/min", end="")
        
        time.sleep(10)  # Update every 10 seconds
    
    print("\n✅ Campaign completed!")
```

#### Live Dashboard
```python
# Simple web dashboard for monitoring
from flask import Flask, jsonify, render_template
from tierII_email_campaign.monitoring import get_campaign_status

app = Flask(__name__)

@app.route('/dashboard')
def dashboard():
    """Campaign monitoring dashboard."""
    return render_template('dashboard.html')

@app.route('/api/status/<campaign_id>')
def campaign_status(campaign_id):
    """Get campaign status API."""
    status = get_campaign_status(campaign_id)
    return jsonify({
        'campaign_id': campaign_id,
        'progress': status.progress,
        'sent': status.sent,
        'failed': status.failed,
        'rate': status.send_rate,
        'eta': status.estimated_completion.isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### Post-Campaign Analytics

#### Campaign Results Analysis
```python
def analyze_campaign_results(campaign_id: str):
    """Comprehensive campaign analysis."""
    
    results = load_campaign_results(campaign_id)
    
    # Basic metrics
    total_sent = results.successful_sends
    total_failed = results.failed_sends
    success_rate = (total_sent / (total_sent + total_failed)) * 100
    
    # Timing analysis
    avg_send_time = results.average_send_time
    total_duration = results.campaign_duration
    
    # Error analysis
    error_breakdown = analyze_errors(results.errors)
    
    # Generate report
    report = {
        'campaign_id': campaign_id,
        'summary': {
            'total_contacts': total_sent + total_failed,
            'successful_sends': total_sent,
            'failed_sends': total_failed,
            'success_rate': f"{success_rate:.2f}%"
        },
        'performance': {
            'average_send_time': f"{avg_send_time:.2f}s",
            'total_duration': str(total_duration),
            'emails_per_minute': results.emails_per_minute
        },
        'errors': error_breakdown
    }
    
    return report
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Authentication Errors
```python
# Problem: MailerSend API authentication fails
# Solution: Verify API token and domain setup

def troubleshoot_authentication():
    """Troubleshoot authentication issues."""
    
    # Check API token
    api_token = os.getenv('TIERII_MAILERSEND_API_TOKEN')
    if not api_token:
        print("❌ TIERII_MAILERSEND_API_TOKEN not set")
        return False
    
    if not api_token.startswith('mlsn.'):
        print("❌ Invalid API token format")
        return False
    
    # Test API connection
    try:
        response = test_mailersend_connection(api_token)
        print("✅ API connection successful")
        return True
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False
```

#### 2. Template Errors
```python
# Problem: Template rendering fails
# Solution: Validate template syntax and variables

def troubleshoot_template(template_path: str, sample_data: Dict):
    """Troubleshoot template issues."""
    
    try:
        # Check if template file exists
        if not Path(template_path).exists():
            print(f"❌ Template file not found: {template_path}")
            return False
        
        # Validate template syntax
        validate_template_syntax(template_path)
        print("✅ Template syntax valid")
        
        # Test with sample data
        rendered = render_template(template_path, sample_data)
        print("✅ Template renders successfully")
        
        # Check for missing variables
        missing_vars = find_missing_variables(template_path, sample_data)
        if missing_vars:
            print(f"⚠️  Missing variables: {missing_vars}")
        
        return True
        
    except Exception as e:
        print(f"❌ Template error: {e}")
        return False
```

#### 3. CSV Data Issues
```python
# Problem: CSV data validation fails
# Solution: Check data format and encoding

def troubleshoot_csv_data(csv_path: str):
    """Troubleshoot CSV data issues."""
    
    try:
        # Check file exists
        if not Path(csv_path).exists():
            print(f"❌ CSV file not found: {csv_path}")
            return False
        
        # Check encoding
        encoding = detect_file_encoding(csv_path)
        print(f"📄 File encoding: {encoding}")
        
        # Load and validate data
        contacts = load_contacts(csv_path)
        print(f"📊 Loaded {len(contacts)} contacts")
        
        # Check required fields
        required_fields = ['email']
        for contact in contacts[:5]:  # Check first 5
            missing = [field for field in required_fields if field not in contact]
            if missing:
                print(f"❌ Missing required fields: {missing}")
                return False
        
        # Check email format
        invalid_emails = [c for c in contacts if not is_valid_email(c.get('email', ''))]
        if invalid_emails:
            print(f"⚠️  Found {len(invalid_emails)} invalid emails")
        
        print("✅ CSV data validation passed")
        return True
        
    except Exception as e:
        print(f"❌ CSV error: {e}")
        return False
```

### Performance Optimization

#### 1. Large Contact Lists
```python
# For lists > 10,000 contacts
LARGE_LIST_CONFIG = {
    'batch_size': 25,           # Smaller batches
    'batch_delay': 60,          # Longer delays
    'max_concurrent': 1,        # No parallel processing
    'memory_limit': '512MB',    # Memory management
    'checkpoint_interval': 100  # Save progress frequently
}
```

#### 2. Rate Limit Optimization
```python
# Optimize for MailerSend rate limits
def optimize_rate_limits(contact_count: int, time_window_hours: int = 24):
    """Calculate optimal batch settings for rate limits."""
    
    # MailerSend limits (adjust based on your plan)
    emails_per_hour = 1000
    emails_per_day = 10000
    
    # Calculate optimal settings
    max_hourly_batches = emails_per_hour // 50  # 50 emails per batch
    optimal_batch_delay = 3600 // max_hourly_batches  # seconds
    
    return {
        'batch_size': 50,
        'batch_delay': optimal_batch_delay,
        'estimated_duration': contact_count / emails_per_hour
    }
```

## 📚 Best Practices

### Campaign Planning
1. **Segment your audience** for better personalization
2. **Test templates** with sample data before full campaigns
3. **Start with small batches** to test deliverability
4. **Monitor bounce rates** and adjust sender reputation
5. **Plan for time zones** when scheduling campaigns

### Email Content
1. **Keep subject lines under 50 characters**
2. **Use clear, actionable CTAs**
3. **Include unsubscribe links** (required by law)
4. **Test on multiple email clients**
5. **Optimize for mobile viewing**

### Technical Best Practices
1. **Use environment variables** for sensitive configuration
2. **Implement proper error handling** and retry logic
3. **Log campaign activities** for debugging and compliance
4. **Regular backup** of contact data and campaign results
5. **Monitor API rate limits** and adjust accordingly

## 📚 Related Documentation

- **[Quick Start Guide](../quick-start.md)** - Get started in 5 minutes
- **[Configuration Reference](../api/configuration.md)** - Complete configuration options
- **[Template System](templates.md)** - Advanced template features
- **[Testing Guide](testing.md)** - Testing campaigns and templates
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions

---

**Campaign Management Version**: 0.1.0  
**Supported Formats**: CSV, JSON (via extensions)  
**Template Engine**: Jinja2-compatible with custom functions