# MailerSend API Setup Guide

Complete guide for setting up MailerSend API integration with domain verification and best practices.

## 📋 Overview

MailerSend is a transactional email service that provides reliable email delivery with advanced analytics. This guide covers everything needed to integrate MailerSend with the TierII Email Campaign system.

## 🚀 Account Setup

### 1. Create MailerSend Account

1. Visit [mailersend.com](https://www.mailersend.com/)
2. Click "Sign Up" and choose your plan:
   - **Free Tier**: 3,000 emails/month
   - **Paid Plans**: Higher limits and advanced features
3. Verify your email address
4. Complete account setup

### 2. Access Dashboard

After account creation:
1. Log into [app.mailersend.com](https://app.mailersend.com/)
2. Complete the onboarding wizard
3. Navigate to the main dashboard

## 🔑 API Token Generation

### Creating Your API Token

1. **Navigate to API Tokens**
   - Dashboard → Settings → API Tokens
   - Click "Create Token"

2. **Configure Token Permissions**
   ```
   Token Name: TierII Email Campaign
   Scopes: 
   ✓ Email send
   ✓ Analytics read (optional)
   ✓ Domains read (optional)
   ```

3. **Save Token Securely**
   - Copy the generated token immediately
   - Store in password manager or secure location
   - **Never commit to version control**

### Token Security Best Practices

```bash
# ✅ Good - Environment variable
TIERII_MAILERSEND_API_TOKEN=ms_token_abc123...

# ❌ Bad - Hardcoded in source
api_token = "ms_token_abc123..."  # Never do this!
```

## 🌐 Domain Verification (Critical)

Domain verification is **required** for email delivery. Unverified domains will result in failed sends.

### 1. Add Your Domain

1. **Navigate to Domains**
   - Dashboard → Domains → Add Domain

2. **Enter Domain Information**
   ```
   Domain: yourdomain.com
   Purpose: Transactional emails
   ```

3. **Choose Verification Method**
   - **DNS Records** (recommended)
   - **HTML File Upload** (alternative)

### 2. DNS Record Setup

MailerSend will provide DNS records to add:

```dns
# Example DNS records (yours will be different)
Type: TXT
Name: _mailersend
Value: ms-domain-verification=abc123def456...

Type: CNAME  
Name: mail._domainkey
Value: mail._domainkey.mailersend.net

Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com
```

### 3. Verification Process

1. **Add DNS Records**
   - Log into your domain registrar/DNS provider
   - Add the provided DNS records exactly as shown
   - Save changes

2. **Wait for Propagation**
   - DNS changes can take 5 minutes to 24 hours
   - Use [DNS checker tools](https://dnschecker.org/) to verify propagation

3. **Verify in MailerSend**
   - Return to MailerSend dashboard
   - Click "Verify Domain"
   - Status should change to "Verified" ✅

### 4. Common DNS Issues

| Issue | Solution |
|-------|----------|
| Records not found | Wait longer for DNS propagation |
| Verification fails | Double-check record values for typos |
| CNAME conflicts | Remove conflicting existing records |
| Multiple TXT records | Combine into single record if required |

## 📧 Sender Configuration

### Setting Up Sender Identity

1. **Configure Sender Email**
   ```bash
   # Must be from verified domain
   TIERII_SENDER_EMAIL=noreply@yourdomain.com
   
   # Optional display name
   TIERII_SENDER_NAME=TierII Campaign Team
   ```

2. **Sender Best Practices**
   - Use professional email addresses
   - Avoid generic names like `admin@` or `test@`
   - Include clear sender identification
   - Use consistent sender across campaigns

### Email Authentication Setup

For maximum deliverability, configure:

1. **SPF Record**
   ```dns
   Type: TXT
   Name: @
   Value: v=spf1 include:mailersend.net ~all
   ```

2. **DKIM Signing**
   - Automatically handled by MailerSend
   - Requires domain verification

3. **DMARC Policy**
   ```dns
   Type: TXT
   Name: _dmarc
   Value: v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
   ```

## 🔧 Integration Configuration

### Environment Variables

Complete MailerSend configuration:

```bash
# Required Configuration
TIERII_SENDER_EMAIL=noreply@yourdomain.com
TIERII_MAILERSEND_API_TOKEN=ms_token_your_actual_token_here
TIERII_SENDER_NAME=Your Company Name

# Optional Advanced Configuration
TIERII_CAMPAIGN_BATCH_SIZE=50          # Emails per batch
TIERII_CAMPAIGN_DELAY_MINUTES=5        # Minutes between batches
TIERII_EMAIL_TEMPLATE_PATH=templates/email_template.html
```

### Testing Configuration

```python
# Test MailerSend connection
from src.auth.authentication_factory import authentication_factory
from src.config.settings import load_settings

settings = load_settings()
auth_manager = authentication_factory.create_manager(
    provider="mailersend",
    settings=settings
)

# This should succeed if properly configured
print("✓ MailerSend authentication successful")
```

## 📊 Monitoring & Analytics

### Dashboard Metrics

Monitor your campaigns through MailerSend dashboard:

- **Delivery Rates**: Successful email delivery percentage
- **Open Rates**: Email open tracking (if enabled)
- **Bounce Rates**: Failed delivery tracking
- **Spam Reports**: Recipient spam complaints

### API Rate Limits

MailerSend enforces rate limits:

```
Free Tier: 
- 3,000 emails/month
- 100 emails/hour

Paid Plans:
- Higher monthly limits
- Increased hourly rates
- Burst capacity available
```

### Webhook Configuration (Optional)

Set up webhooks for real-time delivery tracking:

1. **Dashboard → Webhooks → Add Webhook**
2. **Configure Events**
   ```
   ✓ Email sent
   ✓ Email delivered  
   ✓ Email bounced
   ✓ Email opened (optional)
   ```

3. **Endpoint URL**
   ```
   https://yourdomain.com/webhooks/mailersend
   ```

## 🚨 Troubleshooting

### Common Setup Issues

#### Authentication Errors
```bash
Error: Invalid API token
Solution: 
1. Regenerate token in MailerSend dashboard
2. Verify token has correct permissions
3. Check for extra spaces in .env file
```

#### Domain Verification Failures
```bash
Error: Domain not verified
Solution:
1. Check DNS record propagation
2. Verify exact record values
3. Wait up to 24 hours for DNS updates
4. Contact MailerSend support if persistent
```

#### Sending Failures
```bash
Error: Email sending failed
Causes:
- Unverified sender domain
- Invalid recipient email
- Rate limit exceeded
- Insufficient account credits
```

### Debugging Tools

1. **DNS Verification**
   ```bash
   # Check TXT records
   nslookup -type=TXT _mailersend.yourdomain.com
   
   # Check CNAME records  
   nslookup -type=CNAME mail._domainkey.yourdomain.com
   ```

2. **API Testing**
   ```python
   # Test API connectivity
   python -c "
   from src.auth.mailersend_manager import MailerSendManager
   from src.config.settings import load_settings
   
   settings = load_settings()
   manager = MailerSendManager(settings)
   print('✓ MailerSend API connection successful')
   "
   ```

## 📚 Additional Resources

### MailerSend Documentation
- [Official API Documentation](https://developers.mailersend.com/)
- [Domain Verification Guide](https://www.mailersend.com/help/domain-verification)
- [Email Authentication Setup](https://www.mailersend.com/help/email-authentication)

### Support Channels
- **MailerSend Support**: [support.mailersend.com](https://support.mailersend.com/)
- **Community Forum**: [community.mailersend.com](https://community.mailersend.com/)
- **Status Page**: [status.mailersend.com](https://status.mailersend.com/)

---

**Next Steps**: Once MailerSend is configured, proceed to [Configuration Reference](configuration.md) for complete system setup.