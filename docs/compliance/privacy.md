# Privacy Guidelines

Basic privacy practices for handling contact data in the Cannabis Industry Email Campaign Tool.

## 📊 Data Collection

### What Data We Handle

**Required Contact Information:**
- Email addresses (for sending campaigns)
- Contact IDs (for tracking and deduplication)

**Optional Contact Information:**
- First name (for personalization)
- Last name (for personalization)
- Company name (for business contacts)

**System Data:**
- Campaign send logs
- Email delivery status
- Error logs for troubleshooting

### What We Don't Collect

**Prohibited Data Types:**
- Social Security Numbers
- Credit card information
- Bank account details
- Government ID numbers
- Medical information
- Passwords or authentication credentials

## 🔒 Data Protection

### CSV File Handling

**File Storage:**
```
data/
├── contacts/           # Contact CSV files (not in git)
├── test/              # Test data only
└── templates/         # Email templates
```

**File Security:**
- Store contact files in `data/contacts/` directory
- Set appropriate file permissions (read/write for owner only)
- Never commit contact data to version control
- Use `.gitignore` to exclude contact files

### Email Address Protection

**Safe Handling Practices:**
```python
# Good - Use contact IDs in logs
logger.info(f"Processing contact ID: {contact_id}")

# Bad - Don't log email addresses
logger.info(f"Processing email: {email_address}")
```

**Data Validation:**
- Validate email format before processing
- Remove invalid email addresses from lists
- Check for duplicate emails to avoid spam
- Sanitize input data to prevent injection

## 📝 Data Retention

### Contact Data Lifecycle

**Active Contacts:**
- Keep contact data while actively used in campaigns
- Remove contacts that consistently bounce
- Honor unsubscribe requests immediately

**Campaign Logs:**
- Keep campaign send logs for 90 days
- Keep error logs for troubleshooting (30 days)
- Archive successful campaign data monthly

**Data Cleanup:**
```bash
# Example cleanup commands
find data/logs/ -name "*.log" -mtime +30 -delete
find data/campaigns/ -name "*.csv" -mtime +90 -delete
```

## 🚫 Unsubscribe Handling

### Unsubscribe Process

**Manual Unsubscribes:**
1. Remove email from active contact lists
2. Add to suppression list (`data/suppressed_emails.txt`)
3. Log unsubscribe event with timestamp
4. Don't send future campaigns to suppressed emails

**Suppression List Management:**
```python
# Example suppression list handling
def is_suppressed(email_address):
    with open('data/suppressed_emails.txt', 'r') as f:
        suppressed = f.read().splitlines()
    return email_address.lower() in [e.lower() for e in suppressed]

def add_to_suppression(email_address):
    with open('data/suppressed_emails.txt', 'a') as f:
        f.write(f"{email_address.lower()}\n")
```

## 📧 Email Content Privacy

### Cannabis Industry Considerations

**Content Guidelines:**
- Include clear sender identification
- Add physical business address
- Provide easy unsubscribe mechanism
- Include age verification disclaimers
- Add required state compliance disclaimers

**Template Privacy:**
- Don't include sensitive business information
- Use generic contact information
- Include privacy policy link if available
- Add data handling disclaimers

## 🔍 Logging Privacy

### Safe Logging Practices

**What to Log:**
- Campaign execution events
- Email delivery status (success/failure)
- System errors and exceptions
- API rate limiting events

**What NOT to Log:**
- Full email addresses
- Personal contact information
- API keys or tokens
- Sensitive business data

**Example Safe Logging:**
```python
import logging
import hashlib

def get_email_hash(email):
    """Create hash for logging without exposing email."""
    return hashlib.md5(email.encode()).hexdigest()[:8]

# Safe logging examples
logger.info(f"Campaign sent to {len(contacts)} contacts")
logger.info(f"Email delivery failed for contact hash: {get_email_hash(email)}")
logger.error(f"API error: {error_code} - {error_message}")
```

## 🏛️ Cannabis Compliance

### State Regulations

**General Requirements:**
- Verify recipient age (21+ in most states)
- Include required disclaimers about cannabis products
- Respect state-specific advertising restrictions
- Maintain records for compliance audits

**Email Disclaimers:**
```
This email contains information about cannabis products. 
Must be 21+ to receive. Not for use by minors, pregnant 
or nursing women. Keep out of reach of children and pets.

[Your Business Name]
[Physical Address]
[State License Number]

To unsubscribe: [unsubscribe link]
```

## 📋 Privacy Checklist

### Before Sending Campaigns
- [ ] Contact list validated and cleaned
- [ ] Suppression list checked and applied
- [ ] Email templates include required disclaimers
- [ ] Unsubscribe links are functional
- [ ] Sender information is accurate and complete

### Regular Maintenance
- [ ] Review and clean contact lists monthly
- [ ] Update suppression list with bounces/unsubscribes
- [ ] Archive old campaign data
- [ ] Clean up log files
- [ ] Review email templates for compliance

### Data Handling
- [ ] Contact files stored securely (not in version control)
- [ ] Logs don't contain sensitive information
- [ ] API keys stored in environment variables
- [ ] Test data separated from production data
- [ ] File permissions set appropriately

## 🆘 Privacy Incidents

### If Contact Data is Accidentally Exposed

1. **Immediate Actions:**
   - Stop any ongoing campaigns
   - Secure the exposed data
   - Document the scope of exposure

2. **Assessment:**
   - Determine which contacts were affected
   - Assess potential harm or misuse
   - Check legal notification requirements

3. **Response:**
   - Notify affected contacts if required by law
   - Implement additional security measures
   - Document incident for compliance records
   - Review and improve data handling procedures

### If Unsubscribe Requests are Missed

1. **Immediate Actions:**
   - Stop sending to the affected contact
   - Add to suppression list immediately
   - Send apology email if appropriate

2. **Process Review:**
   - Check unsubscribe handling procedures
   - Verify suppression list is being applied
   - Test unsubscribe links in templates
   - Update procedures to prevent recurrence

---

**Remember:** Cannabis industry regulations vary by state. Always consult with legal counsel to ensure compliance with local laws and regulations.