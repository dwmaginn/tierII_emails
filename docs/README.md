# Documentation Index

This directory contains comprehensive documentation for the TierII Email Campaign Tool.

## Documentation Structure

### 📚 User Documentation
**File**: [`user-documentation.md`](./user-documentation.md)

Complete guide for end users, including:
- **Quick Start Guide**: Installation, setup, and first campaign
- **User Manual**: Feature overview, campaign process, and monitoring
- **Configuration Reference**: Detailed configuration options and environment variables

### 🔧 Technical Documentation  
**File**: [`technical-documentation.md`](./technical-documentation.md)

Comprehensive technical reference, including:
- **API Documentation**: Function signatures, parameters, and error handling
- **Architecture Documentation**: System overview, data flow, and module relationships
- **Database Schema Documentation**: CSV structure, validation rules, and data processing

## Quick Navigation

### For New Users
1. Start with [Quick Start Guide](./user-documentation.md#quick-start-guide)
2. Review [Feature Overview](./user-documentation.md#feature-overview)
3. Follow [Campaign Process](./user-documentation.md#campaign-process)

### For Developers
1. Review [System Overview](./technical-documentation.md#system-overview)
2. Study [API Documentation](./technical-documentation.md#api-documentation)
3. Understand [Data Flow](./technical-documentation.md#data-flow)

### For System Administrators
1. Check [Environment Variables](./user-documentation.md#environment-variables)
2. Configure [Rate Limiting](./user-documentation.md#rate-limiting)
3. Review [MailerSend Integration](./technical-documentation.md#mailersend-integration-architecture)

## Documentation Coverage

### User Documentation Sections
- ✅ Installation steps with `pip install -r requirements.txt`
- ✅ Environment setup with `.env.example` to `.env` process
- ✅ MailerSend setup including account creation and domain verification
- ✅ First campaign execution with test data verification
- ✅ Feature overview covering bulk sending, personalization, and rate limiting
- ✅ Campaign process from CSV preparation to result review
- ✅ CSV requirements with required/optional fields and validation rules
- ✅ Template guide with HTML structure and `{first_name}` placeholder usage
- ✅ Rate limiting configuration and MailerSend limits
- ✅ Monitoring with progress bars, logs, and error handling
- ✅ Configuration reference for `email_config.json` and `rate_config.json`
- ✅ Environment variables documentation
- ✅ Template system with variable substitution and custom creation

### Technical Documentation Sections
- ✅ `parse_contacts_from_csv` API with parameters, returns, and error handling
- ✅ `load_email_config` configuration loading and path resolution
- ✅ `generate_email_summary_report` HTML report generation
- ✅ MailerSend integration patterns with authentication and email building
- ✅ Exception handling including ContactParseError and API errors
- ✅ System overview with data flow from CSV to MailerSend API
- ✅ Architecture documentation with module relationships
- ✅ MailerSend integration with API endpoints and response handling
- ✅ CSV structure documentation with all 24 columns from license data
- ✅ Required fields (Email, Primary Contact Name) and optional metadata
- ✅ Validation rules with email format and name extraction logic
- ✅ Contact parsing with name splitting and data cleaning

## File Locations

```
docs/
├── README.md                    # This index file
├── user-documentation.md        # Complete user guide
└── technical-documentation.md   # Technical reference
```

## Additional Resources

- **Project Root**: [`../README.md`](../README.md) - Project overview and setup
- **Configuration Examples**: 
  - [`../email_config.json`](../email_config.json) - Email campaign configuration
  - [`../rate_config.json`](../rate_config.json) - Rate limiting settings
  - [`../.env.example`](../.env.example) - Environment variable template
- **Source Code**: [`../src/`](../src/) - Implementation details
- **Templates**: [`../templates/`](../templates/) - Email template examples
- **Test Data**: [`../data/test/`](../data/test/) - Sample CSV data

## Getting Help

1. **Quick Issues**: Check the [User Manual](./user-documentation.md#user-manual)
2. **Configuration Problems**: Review [Configuration Reference](./user-documentation.md#configuration-reference)
3. **Technical Issues**: Consult [API Documentation](./technical-documentation.md#api-documentation)
4. **Architecture Questions**: See [Architecture Documentation](./technical-documentation.md#architecture-documentation)