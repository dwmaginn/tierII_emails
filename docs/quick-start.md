# Quick Start Guide

Get your TierII Email Campaign system running in under 5 minutes with this streamlined setup guide.

## ⚡ Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.8+** installed (`python --version`)
- [ ] **Git** for cloning the repository
- [ ] **MailerSend account** (free tier available)
- [ ] **Domain access** for email verification

## 🚀 5-Minute Setup

### Step 1: Clone and Install (1 minute)

```bash
# Clone the repository
git clone <repository-url>
cd tierII_emails

# Install dependencies
pip install -r requirements.txt
```

### Step 2: MailerSend Setup (2 minutes)

1. **Create MailerSend Account**
   - Visit [mailersend.com](https://www.mailersend.com/)
   - Sign up for free account
   - Verify your email address

2. **Get API Token**
   - Go to MailerSend Dashboard → API Tokens
   - Click "Create Token"
   - Copy the generated token (keep it secure!)

3. **Verify Domain** (Critical!)
   - Dashboard → Domains → Add Domain
   - Add your sending domain (e.g., `yourdomain.com`)
   - Follow DNS verification steps
   - Wait for verification (usually 5-15 minutes)

### Step 3: Configure Environment (1 minute)

```bash
# Copy example configuration
cp .env.example .env

# Edit with your details
nano .env  # or use your preferred editor
```

**Minimal Required Configuration:**
```bash
# Required - Your verified sender email
TIERII_SENDER_EMAIL=noreply@yourdomain.com

# Required - Your MailerSend API token
TIERII_MAILERSEND_API_TOKEN=your_api_token_here

# Optional - Test recipient for initial testing
TIERII_TEST_RECIPIENT_EMAIL=your-test@email.com
```

### Step 4: Verify Setup (1 minute)

```bash
# Test configuration loading
python -c "from src.config.settings import TierIISettings; settings = TierIISettings(); print('✓ Configuration loaded successfully')"

# Verify CSV data loading
python scripts/t_csv_reader.py

# Run the main campaign script
python src/email_campaign.py
```

## 🎯 First Campaign Test

### Send Your First Test Email

```bash
# Run the campaign in test mode
python src/email_campaign.py
```

The system will:
1. Load your contact data
2. Show a preview of contacts
3. Send a test email to your configured test recipient
4. Wait for your confirmation before proceeding

### Expected Output

```
✓ MailerSend authentication manager initialized
✓ Loaded 119 contacts from CSV
✓ Test email sent successfully to your-test@email.com
Continue with full campaign? (y/N):
```

## ⚠️ Common Quick Setup Issues

### Issue: "Domain not verified"
**Solution**: Wait for DNS propagation (up to 24 hours) or check DNS records

### Issue: "API token invalid"
**Solution**: Regenerate token in MailerSend dashboard, ensure no extra spaces

### Issue: "CSV file not found"
**Solution**: Verify file path in `.env` or use default location `data/contacts/`

### Issue: "Import errors"
**Solution**: Ensure virtual environment is activated and dependencies installed

## 🔧 Quick Configuration Options

### Batch Processing Settings
```bash
# Process 25 emails per batch (default: 50)
TIERII_CAMPAIGN_BATCH_SIZE=25

# Wait 10 minutes between batches (default: 5)
TIERII_CAMPAIGN_DELAY_MINUTES=10
```

### Custom Template Path
```bash
# Use custom email template
TIERII_EMAIL_TEMPLATE_PATH=templates/custom_template.html
```

## ✅ Verification Checklist

After setup, verify these work:

- [ ] Configuration loads without errors
- [ ] MailerSend authentication succeeds
- [ ] CSV data loads correctly
- [ ] Test email sends successfully
- [ ] Domain verification is complete
- [ ] All tests pass

## 🎉 You're Ready!

Your TierII Email Campaign system is now configured and ready for use.

### Next Steps:
1. **[Campaign Management Guide](guides/campaigns.md)** - Learn to run full campaigns
2. **[CSV Data Format Guide](guides/csv-format.md)** - Prepare your contact data
3. **[Email Templates Guide](guides/templates.md)** - Customize your email content

### Need Help?
- **Configuration Issues**: See [Configuration Reference](api/configuration.md)
- **MailerSend Problems**: Check [MailerSend API Guide](api/mailersend.md)
- **General Troubleshooting**: Visit [Troubleshooting Guide](guides/troubleshooting.md)

---

**⏱️ Total Setup Time**: ~5 minutes  
**✨ You're now ready to send professional email campaigns!**