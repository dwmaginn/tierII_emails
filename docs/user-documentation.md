# User Documentation

## Quick Start Guide

### Installation Steps

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   - Copy `.env.example` to `.env`
   - Fill in required environment variables:
     - `TIERII_SENDER_EMAIL`: Your verified sender email address
     - `TIERII_MAILERSEND_API_TOKEN`: Your MailerSend API token

3. **MailerSend Setup**
   - Create a MailerSend account at [mailersend.com](https://mailersend.com)
   - Generate an API token from the MailerSend dashboard
   - Verify your sender domain in MailerSend settings
   - Add your domain to the approved sender list

4. **First Campaign**
   ```bash
   python -m src.main
   ```
   - The system will use the test data in `data/test/testdata.csv`
   - Check the console for progress updates
   - Review the HTML report generated in the `logs/` directory

### Verification Steps
- Check MailerSend dashboard for delivery statistics
- Review log files for any errors
- Confirm email delivery to test recipients

---

## User Manual

### Feature Overview

The TierII Email Campaign Tool provides:
- **Bulk Email Sending**: Process hundreds of contacts efficiently
- **Personalization**: Automatic first name extraction and insertion
- **Rate Limiting**: Configurable batch processing to respect API limits
- **Progress Tracking**: Real-time progress bars and colored console output
- **HTML Reports**: Comprehensive campaign results with success metrics
- **Error Handling**: Robust error recovery and detailed logging

### Campaign Process

1. **Prepare CSV Data**
   - Ensure your CSV contains required columns (see CSV Requirements below)
   - Validate email addresses and contact names
   - Place CSV file in the `data/` directory

2. **Configure Email Content**
   - Update `email_config.json` with your campaign details
   - Customize the HTML template in `templates/email_template.html`
   - Test template rendering with sample data

3. **Set Rate Limits**
   - Adjust `rate_config.json` based on your MailerSend plan
   - Consider recipient server limits and best practices
   - Test with small batches first

4. **Run Campaign**
   - Execute `python -m src.main`
   - Monitor progress in real-time
   - Do not interrupt the process during sending

5. **Review Results**
   - Check the generated HTML report
   - Review log files for detailed information
   - Analyze success rates and failed contacts

### CSV Requirements

#### Required Columns
- **Email**: Valid email address for the recipient
- **Primary Contact Name**: Full name for personalization (e.g., "John Smith", "Jane Doe")

#### Optional Fields
The system can utilize additional license data columns:
- License Number, Entity Name, Business Website
- Address fields (Street, City, State, ZIP)
- License Type, Status, Expiration Date
- Business categories and operational details

#### Data Validation Rules
- Email addresses must be valid format
- Names are automatically parsed for first name extraction
- Empty or invalid emails are skipped with logging
- Special characters in names are handled gracefully

### Template Guide

#### HTML Structure
- Templates use standard HTML with inline CSS
- Responsive design for mobile compatibility
- Professional styling with cannabis industry theming

#### Personalization Variables
- `{first_name}`: Extracted from Primary Contact Name
- `{name}`: Full contact name
- Additional variables can be added for entity name, license info, etc.

#### Styling Guidelines
- Use inline CSS for maximum email client compatibility
- Maintain professional appearance with consistent branding
- Test templates across different email clients
- Keep file size under 100KB for optimal delivery

### Rate Limiting

#### Configuration Options
- **batch_size**: Number of emails sent before cooldown (default: 10)
- **cooldown**: Seconds to wait between batches (default: 60)
- **individual_cooldown**: Seconds between individual emails (default: 7)

#### MailerSend Limits
- Free tier: 3,000 emails/month
- Paid plans: Higher limits based on subscription
- Rate limits: Varies by plan (typically 10-100 emails/minute)

#### Optimization Tips
- Start with conservative settings and increase gradually
- Monitor MailerSend dashboard for delivery metrics
- Adjust based on recipient server responses
- Consider time zones for optimal delivery times

### Monitoring

#### Progress Tracking
- Real-time progress bars show completion status
- Color-coded console output for different log levels
- Batch processing indicators with timing information

#### Log Files
- Detailed logs saved in `logs/` directory
- Separate files for successful and failed sends
- Timestamped entries for audit trails

#### Error Handling
- Automatic retry logic for temporary failures
- Graceful handling of invalid email addresses
- Detailed error messages for troubleshooting

#### Success Metrics
- Total contacts processed
- Success/failure rates
- Processing time and throughput
- HTML reports with visual summaries

---

## Configuration Reference

### email_config.json

```json
{
    "subject": "Your email subject line",
    "body": "Plain text version with {name} placeholder",
    "html": "templates/email_template.html",
    "attachments": [],
    "contacts": "data/test/testdata.csv"
}
```

#### Configuration Fields
- **subject**: Email subject line (supports variables)
- **body**: Plain text email content with placeholder support
- **html**: Path to HTML template file (relative to project root)
- **attachments**: Array of file paths for email attachments
- **contacts**: Path to CSV file containing contact data

### rate_config.json

```json
{
    "batch_size": 10,
    "cooldown": 60,
    "individual_cooldown": 7
}
```

#### Rate Limiting Fields
- **batch_size**: Emails per batch before cooldown (1-50 recommended)
- **cooldown**: Seconds between batches (30-300 recommended)
- **individual_cooldown**: Seconds between individual emails (5-15 recommended)

### Environment Variables

#### Required Variables
```bash
# Sender email address (must be verified in MailerSend)
TIERII_SENDER_EMAIL=sender@yourdomain.com

# MailerSend API token from dashboard
TIERII_MAILERSEND_API_TOKEN=your_api_token_here
```

#### Optional Variables
```bash
# Custom log level (DEBUG, INFO, WARNING, ERROR)
TIERII_LOG_LEVEL=INFO

# Custom report title for HTML reports
TIERII_REPORT_TITLE="Cannabis Outreach Campaign"

# Override default batch processing
TIERII_BATCH_SIZE=15
TIERII_COOLDOWN=45
```

### Template System

#### Variable Substitution
- Variables use `{variable_name}` format
- Case-sensitive matching
- Automatic HTML escaping for safety
- Fallback to empty string for missing variables

#### HTML vs Text Fallback
- HTML template takes precedence when available
- Plain text body used as fallback
- Both versions support variable substitution
- Consistent styling maintained across formats

#### Custom Template Creation
1. Copy existing template as starting point
2. Maintain responsive design principles
3. Test across multiple email clients
4. Use inline CSS for maximum compatibility
5. Keep total size under 100KB
6. Include unsubscribe links as required by law