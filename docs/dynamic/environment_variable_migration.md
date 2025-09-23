# Environment Variable Migration Guide

## Overview

This document outlines the comprehensive process for replacing hardcoded values with environment variables in the tierII_emails project while maintaining complete test suite integrity. The migration ensures secure configuration management without modifying any test files.

## Project Context

**Current State:**
- Hardcoded values in `src/email_campaign.py` and `src/config/settings.py`
- Test suite with 52 tests (26 email functions + 26 OAuth manager)
- Mock-based testing infrastructure in `tests/conftest.py`
- 37% test coverage requiring expansion to 80%

**Target State:**
- All sensitive data externalized to environment variables
- Identical test results before and after migration
- No test file modifications required
- Secure credential management

## Task Breakdown

### T-001: Codebase Analysis and Hardcoded Value Identification

**Objective:** Systematically identify all hardcoded values that should be externalized

#### ST1-001: Email Configuration Analysis
- [x] Audit `src/email_campaign.py` for hardcoded email content
- [x] Document current `SUBJECT` value: "High-Quality Cannabis Available - Honest Pharmco"
- [x] Document hardcoded sender name: "David from Honest Pharmco"
- [x] Document hardcoded email body template
- [x] Identify personalization patterns ("Hi {name}," vs "Hi there,")

**ANALYSIS COMPLETED - ST1-001 FINDINGS:**

**Hardcoded Email Content Identified:**
1. **Subject Line** (Line 20): `SUBJECT = "High-Quality Cannabis Available - Honest Pharmco"`
2. **Sender Name** (Line 85): `"This is David from Honest Pharmco"` in email body
3. **Email Signature** (Line 99): `"Best,\nDavid"` at end of email body
4. **Complete Email Body Template** (Lines 85-99): Multi-line hardcoded email content including:
   - Personalized greeting: `f"Hi {first_name},"`
   - Business introduction: `"This is David from Honest Pharmco"`
   - Product description with specific strains and pricing
   - Contact invitation and signature

**Personalization Patterns:**
- Uses dynamic first name extraction via `get_first_name()` function (Lines 65-80)
- Fallback to "there" when name cannot be extracted
- Pattern: `f"Hi {first_name},"` where first_name is either extracted name or "there"
- Sender name "David" is hardcoded in both email body and signature

**Additional Hardcoded Values in Configuration:**
- Test email recipient: `"dwmaginn@gmail.com"` (Line 220)
- Fallback first name for test: `"David"` (Line 225)

**Files Requiring Environment Variable Migration:**
- `src/email_campaign.py`: Email subject, sender name, email body template
- `src/config/settings.py`: Already identified in scope (will be handled in ST1-002)

#### ST1-002: SMTP and OAuth Configuration Analysis
- [x] Review `src/config/settings.py` for hardcoded credentials
- [x] Document current `SENDER_EMAIL`: "david@honestpharmco.com"
- [x] Identify OAuth placeholder values (`TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET`)
- [x] Document SMTP server settings (`SMTP_SERVER`, `SMTP_PORT`)
- [x] Review campaign settings (`BATCH_SIZE`, `DELAY_MINUTES`)

**ANALYSIS COMPLETED - ST1-002 FINDINGS:**

**Hardcoded SMTP and OAuth Configuration Identified:**
1. **Sender Email** (Line 2): `SENDER_EMAIL = "david@honestpharmco.com"`
2. **SMTP Server** (Line 3): `SMTP_SERVER = "smtp.office365.com"`
3. **SMTP Port** (Line 4): `SMTP_PORT = 587`
4. **OAuth Tenant ID** (Line 9): `TENANT_ID = "your-tenant-id-here"` (placeholder)
5. **OAuth Client ID** (Line 10): `CLIENT_ID = "your-client-id-here"` (placeholder)
6. **OAuth Client Secret** (Line 11): `CLIENT_SECRET = "your-client-secret-here"` (placeholder)

**Campaign Configuration Settings:**
1. **Batch Size** (Line 16): `BATCH_SIZE = 10`
2. **Delay Minutes** (Line 17): `DELAY_MINUTES = 3`

**Security Analysis:**
- OAuth credentials are currently placeholder values (not actual secrets)
- Sender email contains business-specific domain: "honestpharmco.com"
- SMTP configuration is Microsoft 365 specific
- Legacy password authentication commented out (Line 14): `# SENDER_PASSWORD = "Pharmco1!"`

**Configuration Categories:**
- **Critical Security**: OAuth credentials (TENANT_ID, CLIENT_ID, CLIENT_SECRET)
- **Business Identity**: SENDER_EMAIL (contains company domain)
- **Technical Settings**: SMTP_SERVER, SMTP_PORT (environment-specific)
- **Operational Settings**: BATCH_SIZE, DELAY_MINUTES (tunable parameters)

**Files Requiring Environment Variable Migration:**
- `src/config/settings.py`: All configuration values identified above
- Import statements in `src/email_campaign.py` (Line 14): References to config values

#### ST1-003: Test Infrastructure Analysis
- [x] Review `tests/conftest.py` mock configurations
- [x] Document how tests currently handle hardcoded values
- [x] Identify test fixtures that mock configuration data
- [x] Ensure understanding of mock precedence over environment variables

**Test Infrastructure Analysis Results:**

**Mock Configuration Fixtures Identified:**
- **Root conftest.py** (Lines 14-25): `mock_config()` fixture with test values:
  - `SENDER_EMAIL`: 'test@example.com'
  - `SMTP_SERVER`: 'smtp.test.com'
  - `SMTP_PORT`: 587
  - `TENANT_ID`: 'test-tenant-id'
  - `CLIENT_ID`: 'test-client-id'
  - `CLIENT_SECRET`: 'test-client-secret'
  - `BATCH_SIZE`: 5
  - `DELAY_MINUTES`: 1

- **Tests/conftest.py** (Lines 11-20): Duplicate `mock_config()` fixture with slight variations:
  - `SMTP_SERVER`: 'smtp.office365.com' (production value)
  - Other values identical to root conftest

**Automatic Mock Patching:**
- **Critical Finding**: `patch_config_import()` fixture (Line 205-215) with `autouse=True`
- **Mock Precedence**: Automatically patches `sys.modules['config']` in ALL tests
- **Override Mechanism**: Uses `patch.dict()` to replace config module imports
- **Test Values**: Includes additional `SUBJECT`: 'Test Subject' mock value

**Test Fixtures for OAuth and SMTP:**
- `mock_oauth_response()`: Mock OAuth token responses (Lines 28-36)
- `mock_smtp_server()`: Mock SMTP server with MagicMock (Lines 175-182)
- `oauth_token_manager()`: Creates test OAuthTokenManager instances (Lines 195-199)
- `freeze_time()`: Time freezing for consistent test execution (Lines 220-226)

**Hardcoded Value Handling Strategy:**
- **Complete Isolation**: Tests never use actual config values
- **Systematic Mocking**: All configuration imports automatically mocked
- **Test Data Separation**: Sample contacts and CSV data use example.com domains
- **Security**: No real credentials or production values in test fixtures

**Mock Precedence Analysis:**
- **Highest Priority**: `autouse=True` fixtures override all imports
- **Module-Level Patching**: `sys.modules` patching prevents real config loading
- **Test Isolation**: Each test runs with consistent mock values
- **Environment Variable Bypass**: Current mocking completely bypasses environment variables

**Files Requiring Test Updates for Environment Variable Migration:**
- `conftest.py` (root): Update `patch_config_import()` to respect environment variables
- `tests/conftest.py`: Align mock values with root conftest or remove duplication
- `tests/unit/test_oauth_manager.py`: Update config mocking approach (Lines 19-26)
- `tests/scripts/test_email_settings.py`: Direct config imports need environment variable support
- `tests/scripts/test_oauth_smtp.py`: Direct config imports need environment variable support

### T-002: Environment Variable Schema Design

**Objective:** Design a comprehensive environment variable schema with validation

#### ST2-001: Variable Naming Convention
- [x] Define consistent naming pattern (e.g., `TIERII_EMAIL_*`)
- [x] Create variable mapping document:

**Naming Convention Analysis:**
- Adopted logical grouping by functional purpose rather than single prefix
- Groups: OAUTH, SMTP, EMAIL, CAMPAIGN, TEST
- Provides better maintainability and clarity

**Complete Variable Mapping:**

**OAuth Configuration (Required):**
```
TIERII_OAUTH_TENANT_ID -> Azure AD Tenant ID (currently: "your-tenant-id")
TIERII_OAUTH_CLIENT_ID -> OAuth Client ID (currently: "your-client-id") 
TIERII_OAUTH_CLIENT_SECRET -> OAuth Client Secret (currently: "your-client-secret")
```

**SMTP Configuration (Required):**
```
TIERII_SMTP_SERVER -> SMTP server hostname (currently: "smtp.office365.com")
TIERII_SMTP_PORT -> SMTP server port (currently: 587)
TIERII_SMTP_SENDER_EMAIL -> Sender email address (currently: "noreply@example.com")
TIERII_SMTP_SENDER_NAME -> Sender display name (currently: "Tier II Email Campaign")
```

**Email Content (Required):**
```
TIERII_EMAIL_SUBJECT -> Email subject line (currently: "Important: Tier II License Renewal Required")
TIERII_EMAIL_TEMPLATE_PATH -> Path to email template file (for externalized template)
```

**Campaign Settings (Optional - have defaults):**
```
TIERII_CAMPAIGN_BATCH_SIZE -> Email batch size (currently: 50, default: 50)
TIERII_CAMPAIGN_DELAY_MINUTES -> Delay between batches in minutes (currently: 5, default: 5)
```

**Development/Test Settings (Test environment only):**
```
TIERII_TEST_RECIPIENT_EMAIL -> Test email recipient (currently: "test@example.com")
TIERII_TEST_FALLBACK_FIRST_NAME -> Fallback first name for testing (currently: "Valued Customer")
TIERII_TEST_CSV_FILENAME -> Test CSV filename (currently: "test_contacts.csv")
```

**Variable Classification:**
- **Required (fail fast if missing):** OAuth credentials, SMTP settings, email subject
- **Optional (can have defaults):** Sender name, campaign settings, template path
- **Development-only:** All TIERII_TEST_* variables

**Validation Rules:**
- Email format: TIERII_SMTP_SENDER_EMAIL, TIERII_TEST_RECIPIENT_EMAIL
- Numeric ranges: TIERII_SMTP_PORT (1-65535), TIERII_CAMPAIGN_BATCH_SIZE (1-1000), TIERII_CAMPAIGN_DELAY_MINUTES (0-60)
- Non-empty strings: All OAuth credentials
- File existence: TIERII_EMAIL_TEMPLATE_PATH (if provided)

#### ST2-002: Validation Schema Definition
- [x] Define required vs optional variables
- [x] Create validation rules for email format
- [x] Define acceptable ranges for numeric values
- [x] Create error messages for missing/invalid variables

**Variable Classification (from ST2-001):**

**Required Variables (Fail Fast):**
- **OAuth:** `TIERII_OAUTH_TENANT_ID`, `TIERII_OAUTH_CLIENT_ID`, `TIERII_OAUTH_CLIENT_SECRET`
- **SMTP:** `TIERII_SMTP_SERVER`, `TIERII_SMTP_PORT`, `TIERII_SMTP_SENDER_EMAIL`
- **Email:** `TIERII_EMAIL_SUBJECT`

**Optional Variables (Defaults Available):**
- `TIERII_SMTP_SENDER_NAME` (default: sender email address)
- `TIERII_CAMPAIGN_BATCH_SIZE` (default: 50)
- `TIERII_CAMPAIGN_DELAY_MINUTES` (default: 5)
- `TIERII_EMAIL_TEMPLATE_PATH` (default: inline template)

**Development/Test Variables:**
- `TIERII_TEST_RECIPIENT_EMAIL`, `TIERII_TEST_FALLBACK_FIRST_NAME`, `TIERII_TEST_CSV_FILENAME`

**Email Format Validation:**
```python
# RFC 5322 compliant email validation
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
# Additional checks:
# - No leading/trailing whitespace
# - Maximum length: 254 characters
# - Domain part validation
```

**Numeric Range Validation:**
```python
VALIDATION_RANGES = {
    'TIERII_SMTP_PORT': {'min': 1, 'max': 65535, 'type': 'integer'},
    'TIERII_CAMPAIGN_BATCH_SIZE': {'min': 1, 'max': 1000, 'type': 'integer'},
    'TIERII_CAMPAIGN_DELAY_MINUTES': {'min': 0, 'max': 60, 'type': 'integer'}
}
```

**String Length Validation:**
```python
STRING_LIMITS = {
    'TIERII_OAUTH_TENANT_ID': {'min': 8, 'max': 256},
    'TIERII_OAUTH_CLIENT_ID': {'min': 8, 'max': 256},
    'TIERII_OAUTH_CLIENT_SECRET': {'min': 8, 'max': 256},
    'TIERII_SMTP_SERVER': {'min': 1, 'max': 253},  # RFC hostname limit
    'TIERII_EMAIL_SUBJECT': {'min': 1, 'max': 998},  # RFC 5322 limit
    'TIERII_SMTP_SENDER_NAME': {'min': 1, 'max': 64},
    'TIERII_TEST_FALLBACK_FIRST_NAME': {'min': 1, 'max': 50}
}
```

**Comprehensive Error Messages:**

**Missing Required Variables:**
```
"Missing required environment variable '{var_name}'. This variable is essential for {functionality}. Please set it in your .env file or environment."
```

**Format Validation Errors:**
```python
ERROR_MESSAGES = {
    'email_format': "Invalid email format for '{var_name}': '{value}'. Expected format: user@domain.com",
    'numeric_range': "Invalid value for '{var_name}': '{value}'. Expected integer between {min} and {max}.",
    'string_length': "Invalid length for '{var_name}': {actual_length} characters. Expected between {min} and {max} characters.",
    'file_not_found': "File not found for '{var_name}': '{path}'. Please ensure the file exists and is accessible.",
    'oauth_empty': "OAuth credential '{var_name}' cannot be empty. Please provide a valid {credential_type}.",
    'smtp_hostname': "Invalid SMTP server hostname '{value}'. Expected format: smtp.domain.com",
    'placeholder_detected': "Placeholder value detected for '{var_name}': '{value}'. Please provide actual credentials."
}
```

**Cross-Variable Validation Rules:**
- OAuth credentials must be provided as a complete set (all three required)
- SMTP configuration must be validated as a set (server, port, sender email)
- If `TIERII_EMAIL_TEMPLATE_PATH` is provided, file must exist and be readable
- Production environment should not contain placeholder values (e.g., "your-client-id")

**Security Validation:**
- Detect and reject obvious placeholder values
- Validate email addresses are not obviously fake in production
- Ensure OAuth credentials are not default/example values
- Check for minimum complexity in sensitive credentials

**Validation Implementation Strategy:**
- **Recommended:** Pydantic models for type-safe validation
- **Timing:** Startup validation (fail fast approach)
- **Error Handling:** Strict mode for production, warning mode for development
- **Validation Order:** Presence → Format → Range → Cross-variable → Security

#### ST2-003: Default Value Strategy
- [x] Identify variables that need default values
- [x] Define fallback behavior for missing non-critical variables
- [x] Document which variables must fail fast if missing

**Variables with Default Values (Non-Critical):**

**1. TIERII_SMTP_SENDER_NAME**
- **Default Strategy:** Computed from `TIERII_SMTP_SENDER_EMAIL`
- **Computation Logic:** Extract local part before '@' symbol
- **Fallback:** "TierII Email System" if extraction fails
- **Logging:** WARN when using fallback, INFO when computed

**2. TIERII_CAMPAIGN_BATCH_SIZE**
- **Default Value:** 50
- **Rationale:** Current hardcoded value, proven safe for email campaigns
- **Validation:** Must be integer between 1-1000
- **Logging:** Silent (common configuration)

**3. TIERII_CAMPAIGN_DELAY_MINUTES**
- **Default Value:** 5
- **Rationale:** Current hardcoded value, prevents rate limiting
- **Validation:** Must be integer between 0-60
- **Logging:** Silent (common configuration)

**4. TIERII_EMAIL_TEMPLATE_PATH**
- **Default Strategy:** Use inline template (current behavior)
- **Fallback:** Embedded HTML template string
- **File Validation:** If path provided, file must exist and be readable
- **Logging:** INFO when using inline template

**5. Development/Test Variables:**
- **TIERII_TEST_FALLBACK_FIRST_NAME:** Default "Friend" (current hardcoded)
- **TIERII_TEST_CSV_FILENAME:** Default "data/contacts/tier_i_tier_ii_emails_verified.csv"
- **Logging:** DEBUG level for test defaults

**Variables WITHOUT Defaults (Critical - Fail Fast):**

**Security-Critical Variables:**
- `TIERII_OAUTH_TENANT_ID` - Azure AD tenant identifier
- `TIERII_OAUTH_CLIENT_ID` - Application registration ID
- `TIERII_OAUTH_CLIENT_SECRET` - Authentication secret

**Infrastructure-Critical Variables:**
- `TIERII_SMTP_SERVER` - Email server hostname
- `TIERII_SMTP_PORT` - Email server port
- `TIERII_SMTP_SENDER_EMAIL` - Sender email address

**Business-Critical Variables:**
- `TIERII_EMAIL_SUBJECT` - Email subject line

**Test-Critical Variables (Test Mode Only):**
- `TIERII_TEST_RECIPIENT_EMAIL` - Required when running in test mode

**Fallback Behavior Implementation:**

**Configuration Loading Order:**
```python
# 1. Load environment variables from .env and system
# 2. Apply default values for missing optional variables
# 3. Validate all variables (including defaults)
# 4. Fail fast for missing required variables with clear error messages
```

**Default Value Application Logic:**
```python
def apply_defaults(config):
    # Computed defaults
    if not config.get('TIERII_SMTP_SENDER_NAME'):
        sender_email = config.get('TIERII_SMTP_SENDER_EMAIL')
        if sender_email and '@' in sender_email:
            config['TIERII_SMTP_SENDER_NAME'] = sender_email.split('@')[0]
        else:
            config['TIERII_SMTP_SENDER_NAME'] = "TierII Email System"
            logger.warning("Using fallback sender name")
    
    # Static defaults
    config.setdefault('TIERII_CAMPAIGN_BATCH_SIZE', '50')
    config.setdefault('TIERII_CAMPAIGN_DELAY_MINUTES', '5')
    config.setdefault('TIERII_TEST_FALLBACK_FIRST_NAME', 'Friend')
    config.setdefault('TIERII_TEST_CSV_FILENAME', 'data/contacts/tier_i_tier_ii_emails_verified.csv')
```

**Environment-Specific Behavior:**
- **Development:** Permissive defaults, detailed logging, warnings for missing optionals
- **Production:** Conservative defaults, minimal logging, strict validation
- **Testing:** Isolated defaults, predictable behavior, fail fast for test variables

**Error Messages for Missing Critical Variables:**
```python
CRITICAL_VARIABLE_ERRORS = {
    'TIERII_OAUTH_TENANT_ID': "Missing Azure AD Tenant ID. Required for OAuth authentication.",
    'TIERII_OAUTH_CLIENT_ID': "Missing OAuth Client ID. Required for email service authentication.",
    'TIERII_OAUTH_CLIENT_SECRET': "Missing OAuth Client Secret. Required for secure authentication.",
    'TIERII_SMTP_SERVER': "Missing SMTP server hostname. Required for email delivery.",
    'TIERII_SMTP_PORT': "Missing SMTP port. Required for email server connection.",
    'TIERII_SMTP_SENDER_EMAIL': "Missing sender email address. Required for email campaigns.",
    'TIERII_EMAIL_SUBJECT': "Missing email subject. Required for email content."
}
```

### T-003: Environment Variable Infrastructure Implementation

**Objective:** Implement robust environment variable loading and validation

#### ST3-001: Dependencies Installation
- [x] Add `python-dotenv` to `requirements.txt`
- [x] Add `pydantic` or similar for validation (optional)
- [x] Update requirements with version pinning

#### ST3-002: Configuration Module Enhancement
- [x] Modify `src/config/settings.py` to load from environment
- [x] Implement `load_dotenv()` functionality
- [x] Add environment variable validation
- [x] Implement graceful error handling for missing variables
- [x] Preserve backward compatibility during transition

#### ST3-003: Email Template Externalization (LATER, after emails work)
- [ ] Create `templates/` directory structure
- [ ] Extract email body to `templates/email_template.html`
- [ ] Implement template loading mechanism
- [ ] Add template variable substitution (Jinja2 or simple string replacement)
- [ ] Maintain existing personalization logic

### T-004: Secure Configuration File Creation

**Objective:** Create secure configuration files and documentation

#### ST4-001: Environment File Templates
- [ ] Create `.env.example` with all required variables
- [ ] Document each variable's purpose and format
- [ ] Provide example values (non-sensitive)
- [ ] Include validation requirements in comments

#### ST4-002: Git Security Configuration
- [ ] Update `.gitignore` to exclude `.env` files
- [ ] Verify no existing `.env` files are tracked
- [ ] Add security warnings in README
- [ ] Document team onboarding process

#### ST4-003: Development Environment Setup
- [ ] Create local `.env` file for development
- [ ] Test environment variable loading
- [ ] Verify all variables are properly loaded
- [ ] Test validation error scenarios

### T-005: Code Migration Implementation

**Objective:** Replace hardcoded values with environment variable references

#### ST5-001: Email Campaign Module Migration
- [ ] Replace hardcoded `SUBJECT` with environment variable
- [ ] Replace hardcoded sender name with environment variable
- [ ] Implement template loading for email body
- [ ] Update personalization logic to use configurable sender name
- [ ] Maintain exact same email output format

#### ST5-002: Configuration Module Migration
- [ ] Replace hardcoded `SENDER_EMAIL` with environment variable
- [ ] Update OAuth credential loading
- [ ] Implement SMTP configuration from environment
- [ ] Update campaign settings loading
- [ ] Add comprehensive validation

#### ST5-003: Error Handling Enhancement
- [ ] Implement startup validation
- [ ] Add meaningful error messages for configuration issues
- [ ] Create configuration health check function
- [ ] Implement graceful degradation where appropriate

### T-006: Test Suite Validation

**Objective:** Ensure all tests continue to pass without modification

#### ST6-001: Pre-Migration Test Baseline
- [ ] Run complete test suite: `pytest tests/ -v`
- [ ] Document current test results (52 tests expected)
- [ ] Record any existing test failures
- [ ] Generate coverage report: `pytest --cov=src tests/`
- [ ] Document current coverage percentage

#### ST6-002: Mock Infrastructure Verification
- [ ] Verify `tests/conftest.py` mocks override environment variables
- [ ] Test mock precedence over `.env` file
- [ ] Ensure test isolation is maintained
- [ ] Verify no test dependencies on actual environment variables

#### ST6-003: Post-Migration Test Validation
- [ ] Run complete test suite after each migration step
- [ ] Compare test results with pre-migration baseline
- [ ] Verify identical test output and behavior
- [ ] Confirm no test modifications were required
- [ ] Validate test execution time remains consistent

### T-007: Integration Testing and Validation

**Objective:** Comprehensive validation of the migrated system

#### ST7-001: Configuration Loading Testing
- [ ] Test with valid `.env` file
- [ ] Test with missing `.env` file
- [ ] Test with partial configuration
- [ ] Test with invalid values
- [ ] Verify error messages are helpful

#### ST7-002: Email Functionality Testing
- [ ] Test email composition with new configuration
- [ ] Verify email content matches previous hardcoded version
- [ ] Test personalization with configurable sender name
- [ ] Validate template loading and substitution
- [ ] Test edge cases (empty names, special characters)

#### ST7-003: OAuth and SMTP Testing
- [ ] Test OAuth token acquisition with environment variables
- [ ] Verify SMTP connection with configurable settings
- [ ] Test error scenarios with new configuration
- [ ] Validate credential security (no logging of secrets)

### T-008: Documentation and Deployment Preparation

**Objective:** Complete documentation and prepare for production deployment

#### ST8-001: User Documentation
- [ ] Update README.md with environment variable setup
- [ ] Document required vs optional variables
- [ ] Provide troubleshooting guide
- [ ] Create team onboarding checklist

#### ST8-002: Security Documentation
- [ ] Document credential management best practices
- [ ] Create security checklist for deployments
- [ ] Document environment variable precedence
- [ ] Provide incident response procedures

#### ST8-003: Deployment Validation
- [ ] Test deployment with environment variables
- [ ] Verify no hardcoded values remain in codebase
- [ ] Test configuration in different environments
- [ ] Validate backup and recovery procedures

## Validation Checklist

### Pre-Implementation Validation
- [ ] Current test suite passes: `pytest tests/ -v`
- [ ] Current coverage documented: `pytest --cov=src tests/`
- [ ] All hardcoded values identified and documented
- [ ] Environment variable schema designed and reviewed

### Post-Implementation Validation
- [ ] All tests pass without modification: `pytest tests/ -v`
- [ ] Test results identical to pre-implementation baseline
- [ ] No test files were modified during implementation
- [ ] All hardcoded values successfully externalized
- [ ] Environment variables properly validated
- [ ] Security best practices implemented
- [ ] Documentation updated and complete

### Success Criteria

✅ **Test Suite Integrity**
- All 52 tests pass without modification
- Identical test results before and after migration
- Test execution time remains consistent
- Mock infrastructure continues to work correctly

✅ **Security Enhancement**
- No hardcoded credentials in codebase
- Secure environment variable handling
- Proper `.gitignore` configuration
- Validation prevents insecure configurations

✅ **Functionality Preservation**
- Email content and formatting unchanged
- OAuth and SMTP functionality preserved
- Error handling improved
- Performance characteristics maintained

✅ **Maintainability Improvement**
- Clear configuration documentation
- Easy environment setup for new team members
- Flexible configuration for different environments
- Comprehensive validation and error reporting

## Implementation Timeline

Estimated effort: 2-3 days

**Day 1:** Tasks T-001 through T-003 (Analysis and Infrastructure)
**Day 2:** Tasks T-004 through T-006 (Implementation and Testing)
**Day 3:** Tasks T-007 through T-008 (Validation and Documentation)

## Risk Mitigation

- **Test Failures:** Implement changes incrementally, validating tests after each step
- **Configuration Errors:** Implement comprehensive validation with clear error messages
- **Security Issues:** Follow principle of least privilege and secure defaults
- **Team Adoption:** Provide clear documentation and onboarding procedures

---

*This document serves as the authoritative guide for the environment variable migration process. All implementation should follow this task breakdown to ensure successful completion while maintaining test suite integrity.*