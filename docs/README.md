# TierII Email Campaign Documentation

Welcome to the comprehensive documentation for the TierII Email Campaign system - a Python-based email marketing solution designed for the cannabis industry using MailerSend API.

## 📚 Documentation Index

### 🚀 Getting Started
- **[Quick Start Guide](quick-start.md)** - Get up and running in 5 minutes
- **[Installation & Setup](api/configuration.md)** - Complete setup instructions
- **[MailerSend API Setup](api/mailersend.md)** - Domain verification and API configuration

### 🏗️ Architecture & Development
- **[System Architecture](architecture/overview.md)** - High-level system design and data flow
- **[Authentication System](api/authentication.md)** - Factory pattern and provider extensibility
- **[Development Guide](guides/development.md)** - Code standards, patterns, and best practices
- **[Testing Guide](guides/testing.md)** - Running tests, coverage requirements, and adding new tests

### 📖 User Guides
- **[Campaign Management](guides/campaigns.md)** - Creating and managing email campaigns
- **[CSV Data Format](guides/csv-format.md)** - Contact data requirements and validation
- **[Email Templates](guides/templates.md)** - Template system and variable substitution
- **[Troubleshooting](guides/troubleshooting.md)** - Common issues and solutions

### 🔧 Technical Reference
- **[Configuration Reference](api/configuration.md)** - Complete environment variables guide
- **[Extension Guide](architecture/extensibility.md)** - Adding new email providers
- **[CSV Processing Pipeline](architecture/csv-processing.md)** - Data validation and processing
- **[Batch Processing](architecture/batch-processing.md)** - Optimization and scaling strategies

### 🔒 Compliance & Security
- **[Security Practices](compliance/security.md)** - API key management and secure practices
- **[Email Compliance](compliance/email-compliance.md)** - CAN-SPAM, GDPR guidelines
- **[Privacy Policy](compliance/privacy.md)** - Contact data handling and protection

## 🎯 Quick Navigation

### For New Users
1. Start with [Quick Start Guide](quick-start.md)
2. Follow [MailerSend API Setup](api/mailersend.md)
3. Read [Campaign Management](guides/campaigns.md)

### For Developers
1. Review [System Architecture](architecture/overview.md)
2. Study [Authentication System](api/authentication.md)
3. Follow [Development Guide](guides/development.md)
4. Set up [Testing Environment](guides/testing.md)

### For System Administrators
1. Configure [Security Practices](compliance/security.md)
2. Review [Configuration Reference](api/configuration.md)
3. Implement [Batch Processing](architecture/batch-processing.md) optimization

## 📊 System Overview

The TierII Email Campaign system is built with:

- **Python 3.8+** with modern async/await patterns
- **MailerSend API** for reliable email delivery
- **Pydantic Settings** for configuration validation
- **Factory Pattern** for extensible authentication
- **CSV Processing** with robust validation
- **Batch Processing** with rate limiting
- **Comprehensive Testing** with 80%+ coverage

## 🔄 Documentation Updates

This documentation is maintained alongside the codebase. When contributing:

1. Update relevant documentation for code changes
2. Follow the established documentation structure
3. Include practical examples and code snippets
4. Test all documented procedures
5. Update this index when adding new sections

## 📞 Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Development**: See [Contributing Guidelines](guides/development.md#contributing)
- **Security**: Report security issues privately to the maintainers

---

**Last Updated**: {current_date}  
**Version**: 0.1.0  
**Maintainers**: TierII Emails Team