# Extensibility Guide

Comprehensive guide for extending the TierII Email Campaign system with new providers, data sources, and functionality.

## 📋 Overview

The TierII system is designed with extensibility as a core principle. This guide covers how to add new email providers, data sources, template engines, and other system extensions while maintaining compatibility and following established patterns.

## 🎯 Extension Philosophy

### Design Principles for Extensions

- **Interface Compliance**: All extensions must implement required interfaces
- **Configuration Integration**: Extensions should integrate with the existing configuration system
- **Testing Requirements**: All extensions must include comprehensive tests
- **Documentation Standards**: Extensions require complete documentation
- **Security First**: Extensions must follow security best practices
- **Backward Compatibility**: Extensions should not break existing functionality

### Extension Categories

1. **Email Service Providers** - Add support for new email APIs
2. **Data Sources** - Support different contact data sources
3. **Template Engines** - Enhanced email template processing
4. **Authentication Methods** - New authentication mechanisms
5. **Monitoring & Analytics** - Enhanced tracking and reporting
6. **Compliance Modules** - Industry-specific compliance features

## 📧 Adding New Email Providers

### Step 1: Implement Provider Interface

Create a new provider class that implements the `AuthProvider` interface:

```python
# src/auth/providers/azure_provider.py

from typing import Dict, Any, Optional
from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential

from src.auth.base_provider import AuthProvider, ProviderCapabilities
from src.config.settings import TierIISettings
from src.auth.exceptions import AuthenticationError

class AzureEmailProvider(AuthProvider):
    """Azure Communication Services email provider."""
    
    def __init__(self, settings: TierIISettings):
        self.settings = settings
        self.connection_string = settings.azure_connection_string
        self.sender_email = settings.sender_email
        self._client = None
        
    def authenticate(self) -> bool:
        """Authenticate with Azure Communication Services."""
        try:
            # Create Azure email client
            self._client = EmailClient.from_connection_string(
                self.connection_string
            )
            
            # Test authentication
            return self.test_connection()
            
        except Exception as e:
            logger.error(f"Azure authentication failed: {e}")
            return False
            
    def get_client(self) -> EmailClient:
        """Get authenticated Azure email client."""
        if not self._client:
            if not self.authenticate():
                raise AuthenticationError("Failed to authenticate with Azure")
        return self._client
        
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate Azure-specific configuration."""
        validation_results = {
            'connection_string_present': bool(self.connection_string),
            'connection_string_format': self._validate_connection_string(),
            'sender_email_present': bool(self.sender_email),
            'sender_email_format': '@' in self.sender_email if self.sender_email else False
        }
        
        validation_results['is_valid'] = all(validation_results.values())
        return validation_results
        
    def test_connection(self) -> bool:
        """Test connection to Azure Communication Services."""
        try:
            # Attempt a simple API call to verify connectivity
            # Note: Implement actual Azure API test call
            response = self._client.get_send_status("test-operation-id")
            return True  # If no exception, connection is valid
        except Exception as e:
            logger.warning(f"Azure connection test failed: {e}")
            return False
            
    @property
    def provider_name(self) -> str:
        return "azure"
        
    @property
    def is_configured(self) -> bool:
        """Check if Azure provider is properly configured."""
        validation = self.validate_configuration()
        return validation['is_valid']
        
    @property
    def capabilities(self) -> ProviderCapabilities:
        """Azure Communication Services capabilities."""
        caps = ProviderCapabilities()
        caps.supports_templates = True
        caps.supports_tracking = True
        caps.supports_webhooks = False  # Depends on Azure setup
        caps.supports_bulk_send = True
        caps.max_batch_size = 100
        caps.rate_limit_per_minute = 300  # Azure-specific limits
        return caps
        
    def _validate_connection_string(self) -> bool:
        """Validate Azure connection string format."""
        if not self.connection_string:
            return False
        return 'endpoint=' in self.connection_string.lower()
        
    def send_email(self, to_email: str, subject: str, content: str) -> Dict[str, Any]:
        """Send email via Azure Communication Services."""
        try:
            client = self.get_client()
            
            message = {
                "senderAddress": self.sender_email,
                "recipients": {
                    "to": [{"address": to_email}]
                },
                "content": {
                    "subject": subject,
                    "html": content
                }
            }
            
            poller = client.begin_send(message)
            result = poller.result()
            
            return {
                'success': True,
                'message_id': result.id,
                'status': 'sent'
            }
            
        except Exception as e:
            logger.error(f"Azure email send failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }
```

### Step 2: Add Configuration Support

Extend the settings class to support the new provider:

```python
# src/config/settings.py

class TierIISettings(BaseSettings):
    # Existing configuration...
    
    # Azure Communication Services configuration
    azure_connection_string: Optional[str] = Field(
        None,
        description="Azure Communication Services connection string"
    )
    azure_resource_name: Optional[str] = Field(
        None,
        description="Azure Communication Services resource name"
    )
    
    # Provider selection
    preferred_email_provider: str = Field(
        "mailersend",
        description="Preferred email provider (mailersend, azure, google, smtp)"
    )
    
    class Config:
        env_prefix = "TIERII_"
        
    @validator('azure_connection_string')
    def validate_azure_connection_string(cls, v):
        """Validate Azure connection string format."""
        if v and not v.startswith('endpoint='):
            raise ValueError('Azure connection string must start with "endpoint="')
        return v
```

### Step 3: Register Provider

Register the new provider with the authentication factory:

```python
# src/auth/__init__.py

from .authentication_factory import AuthenticationFactory
from .providers.mailersend_provider import MailerSendAuthProvider
from .providers.azure_provider import AzureEmailProvider

# Initialize factory and register providers
def create_authentication_factory() -> AuthenticationFactory:
    """Create and configure authentication factory with all providers."""
    factory = AuthenticationFactory()
    
    # Register all available providers
    factory.register_provider('mailersend', MailerSendAuthProvider)
    factory.register_provider('azure', AzureEmailProvider)
    
    # Set default provider
    factory.set_default_provider('mailersend')
    
    return factory

# Global factory instance
authentication_factory = create_authentication_factory()
```

### Step 4: Add Provider-Specific Tests

Create comprehensive tests for the new provider:

```python
# tests/auth/providers/test_azure_provider.py

import pytest
from unittest.mock import Mock, patch
from src.auth.providers.azure_provider import AzureEmailProvider
from src.config.settings import TierIISettings

class TestAzureEmailProvider:
    
    @pytest.fixture
    def azure_settings(self):
        """Create test settings for Azure provider."""
        return TierIISettings(
            sender_email="test@example.com",
            azure_connection_string="endpoint=https://test.communication.azure.com/;accesskey=test_key"
        )
        
    @pytest.fixture
    def azure_provider(self, azure_settings):
        """Create Azure provider instance for testing."""
        return AzureEmailProvider(azure_settings)
        
    def test_provider_initialization(self, azure_provider):
        """Test Azure provider initializes correctly."""
        assert azure_provider.provider_name == "azure"
        assert azure_provider.sender_email == "test@example.com"
        
    def test_configuration_validation_success(self, azure_provider):
        """Test successful configuration validation."""
        validation = azure_provider.validate_configuration()
        
        assert validation['is_valid'] is True
        assert validation['connection_string_present'] is True
        assert validation['sender_email_present'] is True
        
    def test_configuration_validation_failure(self):
        """Test configuration validation with missing data."""
        settings = TierIISettings(sender_email="test@example.com")
        provider = AzureEmailProvider(settings)
        
        validation = provider.validate_configuration()
        assert validation['is_valid'] is False
        assert validation['connection_string_present'] is False
        
    @patch('azure.communication.email.EmailClient.from_connection_string')
    def test_authentication_success(self, mock_client, azure_provider):
        """Test successful authentication."""
        mock_client.return_value = Mock()
        
        with patch.object(azure_provider, 'test_connection', return_value=True):
            result = azure_provider.authenticate()
            
        assert result is True
        assert azure_provider._client is not None
        
    @patch('azure.communication.email.EmailClient.from_connection_string')
    def test_authentication_failure(self, mock_client, azure_provider):
        """Test authentication failure handling."""
        mock_client.side_effect = Exception("Connection failed")
        
        result = azure_provider.authenticate()
        assert result is False
        
    def test_capabilities(self, azure_provider):
        """Test provider capabilities are correctly defined."""
        caps = azure_provider.capabilities
        
        assert caps.supports_templates is True
        assert caps.supports_tracking is True
        assert caps.max_batch_size == 100
        assert caps.rate_limit_per_minute == 300
        
    @patch('azure.communication.email.EmailClient')
    def test_send_email_success(self, mock_client, azure_provider):
        """Test successful email sending."""
        # Mock the Azure client and response
        mock_poller = Mock()
        mock_result = Mock()
        mock_result.id = "test-message-id"
        mock_poller.result.return_value = mock_result
        
        mock_client_instance = Mock()
        mock_client_instance.begin_send.return_value = mock_poller
        azure_provider._client = mock_client_instance
        
        result = azure_provider.send_email(
            "recipient@example.com",
            "Test Subject",
            "<h1>Test Content</h1>"
        )
        
        assert result['success'] is True
        assert result['message_id'] == "test-message-id"
        assert result['status'] == 'sent'
        
    @patch('azure.communication.email.EmailClient')
    def test_send_email_failure(self, mock_client, azure_provider):
        """Test email sending failure handling."""
        mock_client_instance = Mock()
        mock_client_instance.begin_send.side_effect = Exception("Send failed")
        azure_provider._client = mock_client_instance
        
        result = azure_provider.send_email(
            "recipient@example.com",
            "Test Subject",
            "<h1>Test Content</h1>"
        )
        
        assert result['success'] is False
        assert 'error' in result
        assert result['status'] == 'failed'
```

### Step 5: Integration Testing

Create integration tests for the new provider:

```python
# tests/integration/test_azure_integration.py

import pytest
from src.auth.authentication_factory import AuthenticationFactory
from src.config.settings import load_settings

class TestAzureIntegration:
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('TIERII_AZURE_CONNECTION_STRING'),
        reason="Azure credentials not available"
    )
    def test_azure_end_to_end(self):
        """Test complete Azure provider workflow."""
        # Load real configuration
        settings = load_settings()
        settings.preferred_email_provider = "azure"
        
        # Create factory and get Azure provider
        factory = AuthenticationFactory()
        authenticator = factory.create_authenticator("azure")
        
        # Test authentication
        assert authenticator.authenticate()
        assert authenticator.test_connection()
        
        # Test email sending (to test recipient)
        if settings.test_recipient_email:
            result = authenticator.send_email(
                settings.test_recipient_email,
                "Azure Provider Test",
                "<h1>Test email from Azure provider</h1>"
            )
            assert result['success'] is True
```

## 🗄️ Adding New Data Sources

### Database Contact Loader

```python
# Future extension: Database contact loading
# Note: Current implementation uses CSV files only

from typing import List, Iterator, Dict, Any
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

class DatabaseContactLoader:
    """Future extension: Load contacts from database instead of CSV files."""
    
    def __init__(self, database_url: str, table_name: str = "contacts"):
        self.database_url = database_url
        self.table_name = table_name
        self.engine = sa.create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def load_contacts(self, query_filter: str = None) -> List[Dict[str, Any]]:
        """Load contacts from database with optional filtering."""
        with self.Session() as session:
            query = f"SELECT * FROM {self.table_name}"
            
            if query_filter:
                query += f" WHERE {query_filter}"
                
            result = session.execute(sa.text(query))
            contacts = []
            
            for row in result:
                contact = {
                    'email': row.email,
                    'first_name': row.first_name,
                    'last_name': row.last_name,
                    'company': getattr(row, 'company', None),
                    # Map other fields as needed
                }
                contacts.append(contact)
                
            return contacts
            
    def load_contacts_streaming(self, batch_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        """Stream contacts in batches for memory efficiency."""
        with self.Session() as session:
            offset = 0
            
            while True:
                query = f"""
                    SELECT * FROM {self.table_name}
                    ORDER BY id
                    LIMIT {batch_size} OFFSET {offset}
                """
                
                result = session.execute(sa.text(query))
                rows = result.fetchall()
                
                if not rows:
                    break
                    
                batch = [
                    {
                        'email': row.email,
                        'first_name': row.first_name,
                        'last_name': row.last_name,
                        'company': getattr(row, 'company', None)
                    }
                    for row in rows
                ]
                
                yield batch
                offset += batch_size
                
    def validate_data_source(self) -> Dict[str, Any]:
        """Validate database connection and table structure."""
        try:
            with self.Session() as session:
                # Test connection
                session.execute(sa.text("SELECT 1"))
                
                # Check table exists
                inspector = sa.inspect(self.engine)
                tables = inspector.get_table_names()
                
                if self.table_name not in tables:
                    return {
                        'is_valid': False,
                        'error': f'Table {self.table_name} not found'
                    }
                    
                # Check required columns
                columns = inspector.get_columns(self.table_name)
                column_names = [col['name'] for col in columns]
                
                required_columns = ['email', 'first_name']
                missing_columns = [col for col in required_columns if col not in column_names]
                
                if missing_columns:
                    return {
                        'is_valid': False,
                        'error': f'Missing required columns: {missing_columns}'
                    }
                    
                return {
                    'is_valid': True,
                    'table_exists': True,
                    'columns': column_names,
                    'row_count': self._get_row_count(session)
                }
                
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e)
            }
            
    def _get_row_count(self, session) -> int:
        """Get total number of contacts in table."""
        result = session.execute(sa.text(f"SELECT COUNT(*) FROM {self.table_name}"))
        return result.scalar()
```

### API Contact Loader

```python
# Future extension: API contact loading
# Note: Current implementation uses CSV files only

import requests
from typing import List, Dict, Any

class APIContactLoader:
    """Future extension: Load contacts from REST API endpoint."""
    
    def __init__(self, api_url: str, api_key: str, headers: Dict[str, str] = None):
        self.api_url = api_url
        self.api_key = api_key
        self.headers = headers or {}
        self.headers['Authorization'] = f'Bearer {api_key}'
        
    def load_contacts(self, endpoint: str = "/contacts") -> List[Dict[str, Any]]:
        """Load contacts from API endpoint."""
        try:
            response = requests.get(
                f"{self.api_url}{endpoint}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            contacts = []
            
            # Handle different API response formats
            contact_data = data.get('contacts', data.get('data', data))
            
            for item in contact_data:
                contact = {
                    'email': item['email'],
                    'first_name': item.get('first_name', ''),
                    'last_name': item.get('last_name', ''),
                    'company': item.get('company', ''),
                    # Map additional fields
                    **{k: v for k, v in item.items() if k not in ['email', 'first_name', 'last_name', 'company']}
                }
                contacts.append(contact)
                
            return contacts
            
        except requests.RequestException as e:
            raise Exception(f"API request failed: {e}")
        except KeyError as e:
            raise Exception(f"Invalid API response format: missing {e}")
            
    def validate_data_source(self) -> Dict[str, Any]:
        """Validate API connectivity and response format."""
        try:
            # Test API connectivity
            response = requests.get(
                f"{self.api_url}/health",  # Health check endpoint
                headers=self.headers,
                timeout=10
            )
            
            api_healthy = response.status_code == 200
            
            # Test contacts endpoint
            contacts_response = requests.get(
                f"{self.api_url}/contacts",
                headers=self.headers,
                params={'limit': 1},  # Just test format
                timeout=10
            )
            
            contacts_accessible = contacts_response.status_code == 200
            
            return {
                'is_valid': api_healthy and contacts_accessible,
                'api_healthy': api_healthy,
                'contacts_accessible': contacts_accessible,
                'response_format_valid': self._validate_response_format(contacts_response)
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e)
            }
            
    def _validate_response_format(self, response) -> bool:
        """Validate API response has expected format."""
        try:
            data = response.json()
            
            # Check if response contains contact data
            contact_data = data.get('contacts', data.get('data', data))
            
            if not isinstance(contact_data, list):
                return False
                
            # Check first contact has required fields
            if contact_data and 'email' not in contact_data[0]:
                return False
                
            return True
            
        except Exception:
            return False
```

## 🎨 Adding New Template Engines

### Advanced Template Engine with Jinja2

```python
# src/templates/advanced_engine.py

from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any, List
from src.templates.base_engine import TemplateEngine

class AdvancedTemplateEngine(TemplateEngine):
    """Advanced template engine with Jinja2 support."""
    
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['currency'] = self._currency_filter
        self.env.filters['date_format'] = self._date_format_filter
        
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render template with advanced features."""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
            
        except Exception as e:
            raise TemplateRenderError(f"Template rendering failed: {e}")
            
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render template from string."""
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
            
        except Exception as e:
            raise TemplateRenderError(f"String template rendering failed: {e}")
            
    def validate_template(self, template_name: str) -> Dict[str, Any]:
        """Validate template syntax and required variables."""
        try:
            template = self.env.get_template(template_name)
            
            # Parse template to find undefined variables
            ast = self.env.parse(template.source)
            undefined_vars = self._find_undefined_variables(ast)
            
            return {
                'is_valid': True,
                'template_exists': True,
                'syntax_valid': True,
                'undefined_variables': undefined_vars
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e)
            }
            
    def _currency_filter(self, value: float, currency: str = 'USD') -> str:
        """Format currency values."""
        return f"${value:,.2f} {currency}"
        
    def _date_format_filter(self, date_value, format_string: str = '%Y-%m-%d') -> str:
        """Format date values."""
        if hasattr(date_value, 'strftime'):
            return date_value.strftime(format_string)
        return str(date_value)
        
    def _find_undefined_variables(self, ast) -> List[str]:
        """Find undefined variables in template AST."""
        # Implementation to parse AST and find undefined variables
        # This is a simplified version
        undefined = []
        # ... AST parsing logic ...
        return undefined
```

## 🔍 Adding Monitoring Extensions

### Advanced Analytics Module

```python
# src/monitoring/analytics.py

from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class CampaignAnalytics:
    """Campaign analytics data structure."""
    campaign_id: str
    start_time: datetime
    end_time: datetime
    total_emails: int
    successful_sends: int
    failed_sends: int
    bounce_rate: float
    open_rate: float
    click_rate: float

class AnalyticsCollector:
    """Collect and analyze campaign performance data."""
    
    def __init__(self, storage_backend: str = "file"):
        self.storage_backend = storage_backend
        self.analytics_data = []
        
    def record_campaign_start(self, campaign_id: str, total_emails: int):
        """Record campaign start event."""
        event = {
            'event_type': 'campaign_start',
            'campaign_id': campaign_id,
            'timestamp': datetime.utcnow().isoformat(),
            'total_emails': total_emails
        }
        self._store_event(event)
        
    def record_email_sent(self, campaign_id: str, email: str, success: bool, error: str = None):
        """Record individual email send event."""
        event = {
            'event_type': 'email_sent',
            'campaign_id': campaign_id,
            'timestamp': datetime.utcnow().isoformat(),
            'email': email,
            'success': success,
            'error': error
        }
        self._store_event(event)
        
    def record_email_opened(self, campaign_id: str, email: str, timestamp: datetime = None):
        """Record email open event (from webhooks)."""
        event = {
            'event_type': 'email_opened',
            'campaign_id': campaign_id,
            'timestamp': (timestamp or datetime.utcnow()).isoformat(),
            'email': email
        }
        self._store_event(event)
        
    def generate_campaign_report(self, campaign_id: str) -> CampaignAnalytics:
        """Generate comprehensive campaign analytics report."""
        events = self._get_campaign_events(campaign_id)
        
        start_events = [e for e in events if e['event_type'] == 'campaign_start']
        send_events = [e for e in events if e['event_type'] == 'email_sent']
        open_events = [e for e in events if e['event_type'] == 'email_opened']
        
        if not start_events:
            raise ValueError(f"No start event found for campaign {campaign_id}")
            
        start_time = datetime.fromisoformat(start_events[0]['timestamp'])
        end_time = datetime.fromisoformat(send_events[-1]['timestamp']) if send_events else start_time
        
        total_emails = start_events[0]['total_emails']
        successful_sends = len([e for e in send_events if e['success']])
        failed_sends = len([e for e in send_events if not e['success']])
        
        # Calculate rates
        open_rate = len(open_events) / max(successful_sends, 1) * 100
        bounce_rate = failed_sends / max(total_emails, 1) * 100
        
        return CampaignAnalytics(
            campaign_id=campaign_id,
            start_time=start_time,
            end_time=end_time,
            total_emails=total_emails,
            successful_sends=successful_sends,
            failed_sends=failed_sends,
            bounce_rate=bounce_rate,
            open_rate=open_rate,
            click_rate=0.0  # Would need click tracking
        )
        
    def _store_event(self, event: Dict[str, Any]):
        """Store event using configured backend."""
        if self.storage_backend == "file":
            self._store_to_file(event)
        elif self.storage_backend == "database":
            self._store_to_database(event)
        # Add other storage backends as needed
        
    def _store_to_file(self, event: Dict[str, Any]):
        """Store event to JSON file."""
        filename = f"analytics_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            with open(filename, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to store analytics event: {e}")
            
    def _get_campaign_events(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Retrieve all events for a specific campaign."""
        # Implementation depends on storage backend
        events = []
        
        if self.storage_backend == "file":
            # Read from JSON files
            pass
        elif self.storage_backend == "database":
            # Query database
            pass
            
        return [e for e in events if e.get('campaign_id') == campaign_id]
```

## 🔧 Extension Configuration

### Dynamic Extension Loading

```python
# src/extensions/loader.py

import importlib
import inspect
from typing import Dict, Any, Type, List
from src.extensions.base import Extension

class ExtensionLoader:
    """Dynamically load and manage system extensions."""
    
    def __init__(self):
        self.loaded_extensions: Dict[str, Extension] = {}
        self.extension_registry: Dict[str, Type[Extension]] = {}
        
    def register_extension(self, name: str, extension_class: Type[Extension]):
        """Register an extension class."""
        if not issubclass(extension_class, Extension):
            raise ValueError(f"Extension {name} must inherit from Extension base class")
            
        self.extension_registry[name] = extension_class
        
    def load_extension(self, name: str, config: Dict[str, Any] = None) -> Extension:
        """Load and initialize an extension."""
        if name not in self.extension_registry:
            raise ValueError(f"Extension {name} not registered")
            
        extension_class = self.extension_registry[name]
        extension_instance = extension_class(config or {})
        
        # Validate extension
        if not extension_instance.validate():
            raise ValueError(f"Extension {name} failed validation")
            
        self.loaded_extensions[name] = extension_instance
        return extension_instance
        
    def load_extensions_from_config(self, config: Dict[str, Any]):
        """Load multiple extensions from configuration."""
        extensions_config = config.get('extensions', {})
        
        for name, ext_config in extensions_config.items():
            if ext_config.get('enabled', False):
                try:
                    self.load_extension(name, ext_config)
                    logger.info(f"Loaded extension: {name}")
                except Exception as e:
                    logger.error(f"Failed to load extension {name}: {e}")
                    
    def discover_extensions(self, package_name: str = "src.extensions"):
        """Automatically discover and register extensions."""
        try:
            package = importlib.import_module(package_name)
            
            for item_name in dir(package):
                item = getattr(package, item_name)
                
                if (inspect.isclass(item) and 
                    issubclass(item, Extension) and 
                    item != Extension):
                    
                    extension_name = item_name.lower().replace('extension', '')
                    self.register_extension(extension_name, item)
                    
        except ImportError as e:
            logger.warning(f"Could not discover extensions in {package_name}: {e}")
            
    def get_loaded_extensions(self) -> List[str]:
        """Get list of currently loaded extensions."""
        return list(self.loaded_extensions.keys())
        
    def unload_extension(self, name: str):
        """Unload an extension."""
        if name in self.loaded_extensions:
            extension = self.loaded_extensions[name]
            extension.cleanup()
            del self.loaded_extensions[name]
```

## 📚 Extension Documentation Template

When creating new extensions, use this documentation template:

```markdown
# [Extension Name] Extension

## Overview
Brief description of what the extension does and why it's useful.

## Installation
```bash
# Any additional dependencies
pip install extension-specific-packages
```

## Configuration
```python
# Configuration example
extension_config = {
    'enabled': True,
    'setting1': 'value1',
    'setting2': 'value2'
}
```

## Usage
```python
# Usage examples
from src.extensions.your_extension import YourExtension

extension = YourExtension(config)
result = extension.process_data(input_data)
```

## API Reference
Document all public methods and their parameters.

## Testing
Describe how to test the extension.

## Compatibility
List compatible system versions and dependencies.
```

## 🧪 Extension Testing Framework

```python
# tests/extensions/test_framework.py

import pytest
from abc import ABC, abstractmethod
from src.extensions.base import Extension

class ExtensionTestCase(ABC):
    """Base test case for extension testing."""
    
    @abstractmethod
    def create_extension(self, config: Dict[str, Any] = None) -> Extension:
        """Create extension instance for testing."""
        pass
        
    @abstractmethod
    def get_test_config(self) -> Dict[str, Any]:
        """Get test configuration for extension."""
        pass
        
    def test_extension_initialization(self):
        """Test extension initializes correctly."""
        extension = self.create_extension(self.get_test_config())
        assert extension is not None
        assert extension.validate()
        
    def test_extension_configuration(self):
        """Test extension handles configuration correctly."""
        config = self.get_test_config()
        extension = self.create_extension(config)
        
        # Test configuration is applied
        for key, value in config.items():
            assert hasattr(extension, key) or key in extension.config
            
    def test_extension_cleanup(self):
        """Test extension cleanup works correctly."""
        extension = self.create_extension(self.get_test_config())
        
        # Should not raise exception
        extension.cleanup()
        
    @pytest.mark.integration
    def test_extension_integration(self):
        """Test extension integrates with main system."""
        # Override in specific extension tests
        pass
```

## 📚 Related Documentation

- **[Architecture Overview](overview.md)** - System architecture and design patterns
- **[Authentication Factory](../api/authentication.md)** - Authentication system details
- **[Development Guide](../guides/development.md)** - Development workflow and standards
- **[Testing Guide](../guides/testing.md)** - Testing strategies and implementation

---

**Extensibility Version**: 0.1.0  
**Extension Framework**: Plugin-based with dynamic loading  
**Compatibility**: Designed for backward compatibility and future growth