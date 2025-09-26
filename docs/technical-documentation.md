# Technical Documentation

## API Documentation

### Core Functions

#### `parse_contacts_from_csv(csv_file_path: str) -> List[Dict[str, Any]]`

**Purpose**: Parse contacts from a CSV file and return as a list of contact dictionaries.

**Parameters**:
- `csv_file_path` (str): Path to the CSV file containing contact data

**Returns**:
- `List[Dict[str, Any]]`: List of contact dictionaries with the following structure:
  ```python
  {
      # Original CSV fields (24 columns from license data)
      "License Number": str,
      "License Type": str,
      "Entity Name": str,
      "Email": str,
      "Primary Contact Name": str,
      "Business Website": str,
      "Address Line 1": str,
      "City": str,
      "State": str,
      # ... (all 24 CSV columns preserved)
      
      # Additional processing fields
      "first_name": str  # Extracted from Primary Contact Name
  }
  ```

**Raises**:
- `ContactParseError`: If the CSV file cannot be read or parsed
- `FileNotFoundError`: If the CSV file doesn't exist

**Error Handling**:
- Invalid email addresses are skipped with warning logs
- Malformed rows are skipped with detailed error messages
- Graceful handling of missing or empty fields
- Automatic first name extraction with fallback logic

---

#### `load_email_config() -> Dict[str, Any]`

**Purpose**: Load email configuration from the JSON file with HTML template integration.

**Parameters**: None

**Returns**:
- `Dict[str, Any]`: Configuration dictionary containing:
  ```python
  {
      "subject": str,           # Email subject line
      "body": str,             # Plain text email content
      "html": str,             # Path to HTML template
      "html_content": str,     # Loaded HTML template content
      "attachments": List[str], # File paths for attachments
      "contacts": str          # Path to CSV contact file
  }
  ```

**Raises**:
- `FileNotFoundError`: If config file or HTML template doesn't exist
- `json.JSONDecodeError`: If the JSON file is malformed

**Path Resolution**:
- Automatically resolves paths relative to project root
- Loads HTML template content into `html_content` field
- Handles missing HTML templates gracefully

---

#### `generate_email_summary_report(...) -> str`

**Purpose**: Generate an HTML summary report for email campaign results and open it in browser.

**Parameters**:
- `total_contacts` (int): Total number of contacts processed
- `successful_count` (int): Number of successful email sends
- `failed_count` (int): Number of failed email sends
- `success_rate` (float): Success rate as a percentage
- `failed_contacts` (List[Dict], optional): List of failed contact details
- `report_title` (str, optional): Title for the report
- `timestamp_override` (str, optional): Override timestamp for testing

**Returns**:
- `str`: Path to the generated HTML report file

**Features**:
- Responsive HTML design with CSS styling
- Statistical summary cards with visual indicators
- Detailed failure analysis table
- Automatic browser opening
- Timestamped file naming for historical tracking

---

#### `send_in_bulk()`

**Purpose**: Main orchestration function for bulk email sending with progress tracking.

**Parameters**: None (uses global configuration)

**Process Flow**:
1. Initialize MailerSend client with API token
2. Parse contacts from configured CSV file
3. Process each contact with progress tracking
4. Apply rate limiting between sends
5. Handle success/failure logging
6. Generate comprehensive HTML report

**Rate Limiting**:
- Individual cooldown between emails (default: 7 seconds)
- Batch processing with configurable delays
- Automatic retry logic for temporary failures

**Error Handling**:
- Comprehensive exception catching and logging
- Failed contact tracking with detailed error information
- Graceful degradation for API failures

---

### MailerSend Integration Patterns

#### Authentication
```python
ms = MailerSendClient(os.getenv('TIERII_MAILERSEND_API_TOKEN'))
```

#### Email Building
```python
email = EmailBuilder() \
    .from_email(sender_email) \
    .to_many([{"email": contact_email, "name": contact_name}]) \
    .subject(subject_line) \
    .html(html_content) \
    .text(plain_text_content) \
    .build()
```

#### Response Handling
- Success: HTTP 202 status code
- Failure: Various error codes with detailed messages
- Exception handling for network and API errors

---

### Exception Classes

#### `ContactParseError(Exception)`
**Purpose**: Custom exception for contact parsing failures
**Usage**: Raised when CSV parsing encounters unrecoverable errors
**Attributes**: Inherits standard Exception attributes with descriptive messages

---

## Architecture Documentation

### System Overview

The TierII Email Campaign Tool follows a modular architecture designed for reliability, maintainability, and scalability:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CSV Input     │───▶│  Contact Parser  │───▶│ Email Builder   │
│ (License Data)  │    │ (csv_reader.py)  │    │ (MailerSend)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ HTML Reports    │◀───│   Main Process   │───▶│ Progress Track  │
│(report_gen.py)  │    │   (main.py)      │    │ (tqdm/logging)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Configuration   │
                       │ (JSON/ENV files) │
                       └──────────────────┘
```

### Data Flow

1. **Input Processing**
   - CSV file loaded and validated
   - Contact data parsed and cleaned
   - Email addresses validated
   - First names extracted from full names

2. **Email Personalization**
   - HTML templates loaded from configuration
   - Variable substitution performed (`{first_name}`, `{name}`)
   - Plain text fallback generated
   - Attachments processed (if configured)

3. **Batch Processing**
   - Contacts processed in configurable batches
   - Rate limiting applied between sends
   - Progress tracking with visual indicators
   - Real-time success/failure logging

4. **Result Aggregation**
   - Success and failure statistics collected
   - Detailed error information preserved
   - HTML reports generated with visual summaries
   - Log files created for audit trails

### Module Relationships

#### Core Modules
- **`main.py`**: Orchestration and workflow management
- **`utils/csv_reader.py`**: Contact data parsing and validation
- **`utils/json_reader.py`**: Configuration management
- **`utils/report_generator.py`**: HTML report generation

#### External Dependencies
- **MailerSend SDK**: Email delivery service integration
- **tqdm**: Progress bar visualization
- **colorama**: Cross-platform colored console output
- **python-dotenv**: Environment variable management

#### Configuration Files
- **`email_config.json`**: Campaign-specific settings
- **`rate_config.json`**: Rate limiting parameters
- **`.env`**: Sensitive credentials and API tokens

### MailerSend Integration Architecture

#### API Endpoints
- **Send Email**: `POST /v1/email` - Primary email sending endpoint
- **Authentication**: Bearer token in Authorization header
- **Rate Limiting**: Enforced at API level with configurable limits

#### Authentication Flow
1. API token loaded from environment variables
2. MailerSend client initialized with token
3. Token validated on first API call
4. Subsequent requests use cached authentication

#### Error Response Handling
- **202 Accepted**: Email queued successfully
- **400 Bad Request**: Invalid email format or missing fields
- **401 Unauthorized**: Invalid or expired API token
- **429 Too Many Requests**: Rate limit exceeded
- **500 Server Error**: MailerSend service issues

---

## Database Schema Documentation

### CSV Data Structure

The system processes cannabis license data with a standardized 24-column structure:

#### Required Fields (Critical for Email Processing)

| Column Name | Data Type | Description | Validation Rules |
|-------------|-----------|-------------|------------------|
| `Email` | String | Contact email address | Valid email format, non-empty |
| `Primary Contact Name` | String | Full contact name | Used for first name extraction |

#### License Information Fields

| Column Name | Data Type | Description | Example Values |
|-------------|-----------|-------------|----------------|
| `License Number` | String | Unique license identifier | "TEST-MICR-25-000001" |
| `License Type` | String | Type of cannabis license | "Adult-Use Microbusiness License" |
| `License Type Code` | String | Abbreviated license code | "OCMMICR" |
| `License Status` | String | Current license status | "Active", "Inactive", "Pending" |
| `License Status Code` | String | Status code | "LICACT" |
| `Issued Date` | String | License issue date | "1/1/2025 0:00" |
| `Effective Date` | String | License effective date | "1/1/2025 0:00" |
| `Expiration Date` | String | License expiration date | "1/1/2027 0:00" |
| `Application Number` | String | Original application ID | "TESTMICR-2024-000001" |

#### Business Information Fields

| Column Name | Data Type | Description | Example Values |
|-------------|-----------|-------------|----------------|
| `Entity Name` | String | Legal business name | "Edwards Test Company LLC" |
| `Address Line 1` | String | Primary address | "123 Test Street" |
| `Address Line 2` | String | Secondary address | Apartment, Suite, etc. |
| `City` | String | Business city | "Rochester" |
| `State` | String | Business state | "NY" |
| `Zip Code` | String | Postal code | "14623" |
| `County` | String | County location | "Monroe" |
| `Region` | String | Regional designation | "Finger Lakes" |
| `Business Website` | String | Company website URL | "www.edwardstest.com" |

#### Operational Fields

| Column Name | Data Type | Description | Example Values |
|-------------|-----------|-------------|----------------|
| `Operational Status` | String | Current operational state | "Active" |
| `Business Purpose` | String | Licensed activities | "Adult-Use Cultivation, Processing, Distribution" |
| `Tier Type` | String | License tier classification | "MICROBUS_INDOOR" |
| `Processor Type` | String | Processing capabilities | "Extraction; Infusing and Blending; Packaging" |

### Data Validation Rules

#### Email Validation
- **Format**: Standard RFC 5322 email format validation
- **Required**: Cannot be empty or null
- **Uniqueness**: Duplicates are processed but logged
- **Sanitization**: Whitespace trimmed, case preserved

#### Name Processing
- **Extraction Logic**: First word becomes `first_name`
- **Title Handling**: Common prefixes (Mr, Mrs, Dr) are stripped
- **Fallback**: Empty string if extraction fails
- **Special Characters**: Preserved in original name, cleaned in first name

#### Address Handling
- **Concatenation**: Multiple address fields joined with commas
- **Empty Fields**: Skipped in address building
- **Validation**: No format validation, stored as-is
- **Usage**: Available for template personalization

### Contact Parsing Logic

#### Input Processing
```python
# Raw CSV row example
{
    "License Number": "TEST-MICR-25-000001",
    "Entity Name": "Edwards Test Company LLC",
    "Primary Contact Name": "Mr. Luke Edwards",
    "Email": "edwards.lukec@gmail.com",
    # ... other fields
}
```

#### Output Structure
```python
# Processed contact dictionary
{
    # All original CSV fields preserved exactly
    "License Number": "TEST-MICR-25-000001",
    "Entity Name": "Edwards Test Company LLC",
    "Primary Contact Name": "Mr. Luke Edwards",
    "Email": "edwards.lukec@gmail.com",
    # ... all 24 original columns
    
    # Additional processing fields
    "first_name": "Luke"  # Extracted and cleaned
}
```

#### Error Recovery
- **Invalid Emails**: Row skipped, warning logged
- **Missing Names**: Empty first_name, processing continues
- **Malformed Data**: Individual field errors don't stop processing
- **Encoding Issues**: UTF-8 handling with fallback options

### Data Flow Validation

#### Input Validation
1. File existence check
2. CSV format validation
3. Header row verification
4. Required column presence

#### Processing Validation
1. Email format validation per row
2. Name extraction with error handling
3. Data type consistency checks
4. Field length validation (for email limits)

#### Output Validation
1. Contact count verification
2. Success rate calculation
3. Error categorization and reporting
4. Data integrity checks for reporting