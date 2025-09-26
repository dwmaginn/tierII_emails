# Security Guidelines

Basic security practices for the Cannabis Industry Email Campaign Tool.

## 🔐 API Key Security

### MailerSend API Key Protection

**Environment Variables:**
```bash
# .env file
MAILERSEND_API_TOKEN=your_mailersend_api_key_here
```

**Security Checklist:**
- ✅ Store API keys in `.env` file (never in code)
- ✅ Add `.env` to `.gitignore`
- ✅ Use different API keys for development/production
- ✅ Rotate API keys periodically
- ✅ Never log API keys in application logs

## 📊 Data Security

### Contact Data Protection

**CSV File Security:**
- Store contact CSV files in `data/contacts/` directory
- Limit access to contact files (file permissions)
- Don't commit contact data to version control
- Use test data in `data/test/` for development

**Email Address Handling:**
- Validate email addresses before sending
- Don't log full email addresses in production logs
- Remove invalid emails from contact lists

## 🌐 Network Security

### HTTPS Requirements
- Use HTTPS for all MailerSend API calls (handled by MailerSend SDK)
- Verify SSL certificates in production
- Use secure connections for any external integrations

### Rate Limiting
- Respect MailerSend API rate limits
- Implement retry logic with exponential backoff
- Monitor API usage to avoid hitting limits

## 🔍 Logging Security

### Safe Logging Practices
```python
# Good - Don't log sensitive data
logger.info(f"Sending email to contact ID: {contact_id}")

# Bad - Don't do this
logger.info(f"Sending email to: {email_address}")
```

**Logging Guidelines:**
- Log campaign events and errors
- Don't log email addresses or personal data
- Use contact IDs or hashed identifiers instead
- Rotate log files regularly

## 🚨 Cannabis Industry Compliance

### Legal Considerations
- Ensure compliance with state cannabis regulations
- Verify recipient consent before sending emails
- Include required disclaimers in email content
- Maintain records of email campaigns for compliance audits

### Email Content Security
- Review email templates for compliance
- Include unsubscribe links in all emails
- Add required legal disclaimers
- Verify sender information is accurate

## 🛡️ Development Security

### Code Security
- Keep dependencies updated (`pip install -U -r requirements.txt`)
- Run security scans on dependencies
- Use virtual environments for isolation
- Follow secure coding practices

### Testing Security
- Use test data only in development
- Don't use production API keys in tests
- Mock external API calls in unit tests
- Clean up test data after test runs

## 📋 Security Checklist

### Before Deployment
- [ ] API keys stored in environment variables
- [ ] `.env` file not committed to repository
- [ ] Contact data files secured and not in version control
- [ ] Email templates reviewed for compliance
- [ ] Logging configured to avoid sensitive data
- [ ] Dependencies updated and scanned for vulnerabilities

### Regular Maintenance
- [ ] Rotate API keys quarterly
- [ ] Review and clean up old log files
- [ ] Update dependencies monthly
- [ ] Monitor API usage and costs
- [ ] Review email campaign compliance

## 🆘 Incident Response

### If API Key is Compromised
1. Immediately revoke the compromised key in MailerSend dashboard
2. Generate new API key
3. Update environment variables
4. Review recent API usage for unauthorized activity
5. Update any affected systems

### If Contact Data is Exposed
1. Assess scope of data exposure
2. Notify affected contacts if required by law
3. Review and strengthen data protection measures
4. Document incident for compliance records

---

**Remember:** This is a cannabis industry tool - always prioritize compliance with local and state regulations.