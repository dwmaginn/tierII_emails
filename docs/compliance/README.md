# Compliance Overview

This document provides a simple overview of compliance practices for the Cannabis Industry Email Campaign Tool.

## Quick Compliance Checklist

### Before Running Campaigns
- [ ] API key is stored in `.env` file (never in code)
- [ ] Contact CSV file is in secure location
- [ ] Email template includes physical address
- [ ] Unsubscribe process is documented
- [ ] Cannabis disclaimers are included in templates

### During Campaign Execution
- [ ] Rate limiting is enabled (respects MailerSend limits)
- [ ] Error logging is active but doesn't log sensitive data
- [ ] Campaign progress is monitored
- [ ] Failed sends are tracked for retry

### After Campaign Completion
- [ ] Campaign logs are reviewed
- [ ] Unsubscribe requests are processed
- [ ] Contact list is updated with opt-outs
- [ ] Results are documented

## Key Compliance Areas

### 1. Email Marketing Compliance
- **CAN-SPAM Act**: All emails include sender identification, truthful subject lines, physical address, and clear unsubscribe mechanism
- **Cannabis Industry**: State-specific regulations vary - ensure compliance with local laws

### 2. Data Security
- **API Keys**: Stored securely in environment variables
- **Contact Data**: CSV files handled securely, not logged in plain text
- **Access Control**: Limit who can access contact lists and API keys

### 3. Privacy Protection
- **Data Minimization**: Only collect necessary contact information
- **Retention**: Don't keep contact data longer than needed
- **Unsubscribes**: Honor opt-out requests promptly

## Documentation References

- [Security Practices](./security.md) - Basic security guidelines
- [Privacy Practices](./privacy.md) - Data handling and privacy guidelines
- [Campaign Guide](../guides/campaigns.md) - How to run compliant campaigns

## Cannabis Industry Considerations

### State Regulations
- Research local cannabis marketing laws before sending campaigns
- Some states have strict email marketing restrictions
- Age verification may be required for recipients

### Content Guidelines
- Include appropriate disclaimers about cannabis products
- Follow advertising restrictions for your jurisdiction
- Ensure content complies with platform policies

## Incident Response

### If API Key is Compromised
1. Immediately revoke the compromised key in MailerSend dashboard
2. Generate new API key
3. Update `.env` file with new key
4. Review recent campaign logs for suspicious activity

### If Contact Data is Exposed
1. Assess scope of exposure
2. Notify affected contacts if required by law
3. Review and improve data handling procedures
4. Document incident and response actions

## Regular Maintenance

### Weekly
- Review campaign logs for errors or issues
- Process any unsubscribe requests
- Update suppression list

### Monthly
- Review API key security
- Clean up old campaign logs
- Update contact lists with opt-outs

### Quarterly
- Review compliance procedures
- Update cannabis regulations knowledge
- Audit data handling practices

---

*This compliance overview is designed for the basic cannabis email campaign tool. For enterprise-level compliance requirements, consult with legal and compliance professionals.*