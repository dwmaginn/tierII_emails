# Architecture Overview

Comprehensive overview of the TierII Email Campaign system architecture, design patterns, and component interactions.

## 📋 System Overview

The TierII Email Campaign system is a modular, extensible Python application designed for reliable, compliant email marketing campaigns in the cannabis industry. Built with a focus on security, scalability, and regulatory compliance.

### Key Design Principles

- **Modular Architecture**: Loosely coupled components for easy testing and extension
- **Configuration-Driven**: Environment-based configuration with validation
- **Provider Agnostic**: Pluggable email service providers via factory pattern
- **Security First**: Built-in security practices and compliance features
- **Test-Driven**: Comprehensive testing strategy with 80%+ coverage
- **Observability**: Structured logging and error handling throughout

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TierII Email Campaign System                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   CLI Interface │    │  Configuration  │    │   Logging   │ │
│  │                 │    │   Management    │    │ & Monitoring│ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│           │                       │                     │       │
│           ▼                       ▼                     ▼       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                Campaign Management Layer                    │ │
│  │  ┌─────────────────┐    ┌─────────────────┐               │ │
│  │  │ Email Campaign  │    │ Template Engine │               │ │
│  │  │   Controller    │    │ & Personalization│              │ │
│  │  └─────────────────┘    └─────────────────┘               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                       │                             │
│           ▼                       ▼                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Data Processing Layer                     │ │
│  │  ┌─────────────────┐    ┌─────────────────┐               │ │
│  │  │   CSV Reader    │    │ Contact Data    │               │ │
│  │  │ & Validation    │    │   Validation    │               │ │
│  │  └─────────────────┘    └─────────────────┘               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                       │                             │
│           ▼                       ▼                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                Authentication & Provider Layer              │ │
│  │  ┌─────────────────┐    ┌─────────────────┐               │ │
│  │  │ Authentication  │    │   Email Service │               │ │
│  │  │    Factory      │    │    Providers    │               │ │
│  │  └─────────────────┘    └─────────────────┘               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                       │                             │
│           ▼                       ▼                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    External Services                        │ │
│  │  ┌─────────────────┐    ┌─────────────────┐               │ │
│  │  │   MailerSend    │    │  Future: Google │               │ │
│  │  │      API        │    │  Azure, SMTP    │               │ │
│  │  └─────────────────┘    └─────────────────┘               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Architecture

### Campaign Execution Flow

```
1. Configuration Loading
   ├── Environment Variables (.env)
   ├── Pydantic Validation
   └── Settings Object Creation

2. Contact Data Processing
   ├── CSV File Loading
   ├── Data Validation & Sanitization
   ├── Contact Dictionary Creation
   └── Batch Preparation

3. Authentication & Provider Setup
   ├── Provider Factory Initialization
   ├── Authentication Provider Selection
   ├── API Client Creation
   └── Connection Testing

4. Campaign Execution
   ├── Template Loading & Personalization
   ├── Batch Processing with Rate Limiting
   ├── Email Sending via Provider API
   ├── Progress Tracking & Logging
   └── Error Handling & Retry Logic

5. Monitoring & Reporting
   ├── Success/Failure Tracking
   ├── Performance Metrics
   ├── Error Reporting
   └── Campaign Completion Summary
```

### Detailed Data Flow Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    .env     │───▶│  Settings   │───▶│ Validation  │
│   Config    │    │   Loading   │    │  & Parsing  │
└─────────────┘    └─────────────┘    └─────────────┘
                            │
                            ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ CSV Contact │───▶│   Contact   │───▶│   Batch     │
│    Data     │    │ Dictionary  │    │ Preparation │
└─────────────┘    └─────────────┘    └─────────────┘
                            │
                            ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Auth Factory│───▶│  Provider   │───▶│ API Client  │
│ Initialization   │ Selection   │    │ Creation    │
└─────────────┘    └─────────────┘    └─────────────┘
                            │
                            ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Template   │───▶│ Email       │───▶│   Batch     │
│  Loading    │    │ Personalization  │  Sending    │
└─────────────┘    └─────────────┘    └─────────────┘
                            │
                            ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Progress   │◀───│   Error     │◀───│  Campaign   │
│  Tracking   │    │  Handling   │    │ Completion  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🧩 Component Architecture

### Core Components

#### 1. Configuration Management (`src/config/`)

```python
# Configuration Layer Architecture
src/config/
├── settings.py          # Pydantic settings with validation
├── __init__.py         # Configuration loading utilities
└── validation.py       # Custom validation rules
```

**Responsibilities:**
- Environment variable loading and validation
- Configuration object creation with type safety
- Default value management
- Configuration testing and diagnostics

**Key Features:**
- Pydantic-based validation with detailed error messages
- Environment-specific configuration support
- Secure handling of sensitive configuration data
- Configuration change detection and reloading

#### 2. Authentication System (`src/auth/`)

```python
# Authentication Layer Architecture
src/auth/
├── authentication_factory.py    # Factory pattern implementation
├── base_provider.py            # Abstract provider interface
├── providers/
│   ├── mailersend_provider.py  # MailerSend implementation
│   ├── smtp_provider.py        # Future: SMTP implementation
│   └── google_provider.py      # Future: Google Workspace
└── exceptions.py               # Authentication-specific exceptions
```

**Responsibilities:**
- Provider registration and discovery
- Authentication provider selection and fallback
- API client creation and management
- Connection testing and validation

**Key Features:**
- Factory pattern for extensible provider support
- Automatic provider detection and configuration
- Graceful fallback mechanisms
- Provider capability detection

#### 3. Utilities (`src/utils/`)

```python
# Utilities Layer Architecture
src/utils/
├── csv_reader.py              # CSV file processing
└── __init__.py               # Package initialization
```

**Responsibilities:**
- CSV file loading and parsing
- Contact data validation
- Basic data processing utilities

**Key Features:**
- CSV parsing with error handling
- Email format validation
- File existence checking
- Basic error reporting

#### 4. Email Campaign (`src/email_campaign.py`)

```python
# Main Campaign Module
src/email_campaign.py          # Main campaign controller and execution
```

**Responsibilities:**
- Campaign orchestration and execution
- Email template processing
- Batch processing with delays
- Progress tracking and reporting

**Key Features:**
- Configurable batch processing with delays
- Basic template personalization
- Console progress tracking
- Error handling and logging

### EmailCampaign Class

The main campaign controller that orchestrates the entire email sending process.

```python
# src/email_campaign.py

class EmailCampaign:
    """
    Main email campaign controller.
    
    Handles contact loading, authentication, template processing,
    and batch email sending with configurable delays.
    """
    
    def __init__(self, auth_manager, batch_size=None, delay_minutes=None):
        """
        Initialize campaign with authentication manager.
        
        Args:
            auth_manager: Authentication manager instance
            batch_size: Number of emails per batch (optional)
            delay_minutes: Delay between batches in minutes (optional)
        """
        
    def load_contacts(self, csv_file_path):
        """Load contacts from CSV file as dictionaries."""
        
    def send_campaign(self):
        """Execute the email campaign with batch processing."""
```

### Component Interaction Patterns

#### 1. Dependency Injection Pattern

```python
# Example: Campaign Controller with Injected Dependencies
class EmailCampaign:
    def __init__(
        self,
        csv_file: str,
        batch_size: int = 10,
        delay_minutes: int = 1
    ):
        self.csv_file = csv_file
        self.batch_size = batch_size
        self.delay_minutes = delay_minutes
```

#### 2. Factory Pattern for Providers

```python
# Provider creation through factory
factory = AuthenticationFactory()
authenticator = factory.create_authenticator()  # Auto-selects best provider
```

#### 3. Observer Pattern for Progress Tracking

```python
# Progress tracking with observer pattern
class CampaignProgressTracker:
    def __init__(self):
        self._observers = []
        
    def add_observer(self, observer):
        self._observers.append(observer)
        
    def notify_progress(self, progress_data):
        for observer in self._observers:
            observer.on_progress_update(progress_data)
```

## 🔧 Configuration Architecture

### Configuration Hierarchy

```
Configuration Sources (Priority Order):
1. Environment Variables (TIERII_*)
2. .env File (project root)
3. Default Values (in code)
4. Runtime Overrides (testing)
```

### Configuration Flow

```python
# Configuration loading and validation flow
def load_configuration():
    """Load and validate configuration from multiple sources."""
    
    # 1. Load environment variables
    env_vars = load_environment_variables()
    
    # 2. Load .env file if present
    env_file_vars = load_env_file()
    
    # 3. Merge with defaults
    config_dict = merge_configurations(env_vars, env_file_vars, defaults)
    
    # 4. Validate with Pydantic
    settings = TierIISettings(**config_dict)
    
    # 5. Post-validation checks
    validate_configuration_consistency(settings)
    
    return settings
```

### Configuration Validation Pipeline

```
Input Validation:
├── Type Checking (Pydantic)
├── Format Validation (email, URLs)
├── Range Validation (batch sizes, delays)
├── File Existence Checks
├── API Connectivity Tests
└── Security Validation (no hardcoded secrets)
```

## 🔐 Security Architecture

### Security Layers

```
Security Implementation:
├── Configuration Security
│   ├── Environment variable validation
│   ├── Secret detection and prevention
│   └── Secure defaults enforcement
├── Authentication Security
│   ├── API token validation
│   ├── Connection encryption (TLS)
│   └── Token rotation support
├── Data Security
│   ├── Input validation and sanitization
│   ├── PII handling and protection
│   └── Secure data transmission
└── Operational Security
    ├── Structured logging (no secrets)
    ├── Error handling (no information leakage)
    └── Audit trail maintenance
```

### Security Controls

#### 1. Input Validation

```python
# Comprehensive input validation
class ContactValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format and security."""
        # Format validation
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return False
            
        # Security checks
        if any(char in email for char in ['<', '>', '"', "'"]):
            return False  # Prevent injection
            
        return True
```

#### 2. Secret Management

```python
# Secure configuration handling
class SecureSettings:
    def __init__(self):
        # Never log or display API tokens
        self._api_token = os.getenv('TIERII_MAILERSEND_API_TOKEN')
        
    def get_masked_token(self) -> str:
        """Get masked token for logging."""
        if not self._api_token:
            return "NOT_SET"
        return f"{self._api_token[:8]}...{self._api_token[-4:]}"
```

## 📊 Performance Architecture

### Performance Considerations

#### 1. Batch Processing Optimization

```python
# Optimized batch processing
class BatchProcessor:
    def __init__(self, batch_size: int, delay_minutes: int):
        self.batch_size = min(batch_size, 100)  # Respect API limits
        self.delay_seconds = delay_minutes * 60
        
    async def process_batches(self, contacts: List[Dict[str, Any]]):
        """Process contacts in optimized batches."""
        for batch in self.create_batches(contacts):
            await self.send_batch(batch)
            await asyncio.sleep(self.delay_seconds)
```

#### 2. Memory Management

```python
# Memory-efficient contact processing
def load_contacts_streaming(csv_path: str) -> Iterator[Dict[str, Any]]:
    """Load contacts with streaming to minimize memory usage."""
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            yield dict(row)
```

#### 3. Connection Pooling

```python
# Efficient API client management
class ProviderClientManager:
    def __init__(self):
        self._client_pool = {}
        
    def get_client(self, provider_name: str):
        """Get or create client with connection reuse."""
        if provider_name not in self._client_pool:
            self._client_pool[provider_name] = self._create_client(provider_name)
        return self._client_pool[provider_name]
```

## 🧪 Testing Architecture

### Testing Strategy

```
Testing Pyramid:
├── Unit Tests (70%)
│   ├── Component isolation
│   ├── Mock external dependencies
│   └── Fast execution (<1s per test)
├── Integration Tests (20%)
│   ├── Component interaction
│   ├── Database/API integration
│   └── Test containers for isolation
└── End-to-End Tests (10%)
    ├── Full workflow testing
    ├── Real API integration (sandbox)
    └── Performance validation
```

### Test Architecture

```python
# Test organization structure
tests/
├── unit/
│   ├── test_config/
│   ├── test_auth/
│   ├── test_data/
│   └── test_campaign/
├── integration/
│   ├── test_email_providers/
│   ├── test_csv_processing/
│   └── test_campaign_flow/
├── e2e/
│   ├── test_full_campaign/
│   └── test_provider_fallback/
├── fixtures/
│   ├── test_data.csv
│   ├── mock_responses.json
│   └── test_templates/
└── conftest.py  # Shared test configuration
```

## 🔍 Monitoring & Observability

### Logging Architecture

```python
# Structured logging implementation
import structlog

logger = structlog.get_logger(__name__)

class CampaignLogger:
    def log_campaign_start(self, campaign_id: str, contact_count: int):
        logger.info(
            "campaign_started",
            campaign_id=campaign_id,
            contact_count=contact_count,
            timestamp=datetime.utcnow().isoformat()
        )
        
    def log_batch_sent(self, batch_id: str, success_count: int, error_count: int):
        logger.info(
            "batch_completed",
            batch_id=batch_id,
            success_count=success_count,
            error_count=error_count,
            timestamp=datetime.utcnow().isoformat()
        )
```

### Metrics Collection

```python
# Performance metrics tracking
class CampaignMetrics:
    def __init__(self):
        self.start_time = None
        self.emails_sent = 0
        self.errors_encountered = 0
        self.batches_processed = 0
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        duration = datetime.utcnow() - self.start_time
        
        return {
            'duration_seconds': duration.total_seconds(),
            'emails_sent': self.emails_sent,
            'errors_encountered': self.errors_encountered,
            'batches_processed': self.batches_processed,
            'emails_per_minute': self.emails_sent / (duration.total_seconds() / 60),
            'error_rate': self.errors_encountered / max(self.emails_sent, 1)
        }
```

## 🚀 Extensibility Architecture

### Extension Points

The system is designed with multiple extension points for future enhancements:

#### 1. Email Provider Extensions

```python
# Adding new email providers
class AzureEmailProvider(AuthProvider):
    """Azure Communication Services email provider."""
    
    def authenticate(self) -> bool:
        # Implement Azure-specific authentication
        pass
        
    def get_client(self):
        # Return Azure email client
        pass
```

#### 2. Data Source Extensions

```python
# Adding new data sources
class DatabaseContactLoader:
    """Load contacts from database instead of CSV."""
    
    def load_contacts(self) -> List[Dict[str, Any]]:
        # Implement database loading
        pass
```

#### 3. Template Engine Extensions

```python
# Adding advanced template features
class AdvancedTemplateEngine(TemplateEngine):
    """Template engine with conditional logic and loops."""
    
    def render_template(self, template: str, context: Dict) -> str:
        # Implement advanced template rendering
        pass
```

## 📚 Related Documentation

- **[Authentication Factory](authentication.md)** - Detailed authentication system documentation
- **[Configuration Reference](configuration.md)** - Complete configuration guide
- **[Development Guide](../guides/development.md)** - Development workflow and standards
- **[Testing Guide](../guides/testing.md)** - Testing strategies and implementation

---

**Architecture Version**: 0.1.0  
**Design Pattern**: Modular, Factory-based, Configuration-driven  
**Scalability**: Designed for horizontal scaling and provider diversity