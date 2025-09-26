# Authentication System

Simple authentication system for the TierII Email Campaign using a factory pattern to support multiple email service providers.

## 📋 Overview

The authentication system provides a unified interface for different email service providers, currently supporting MailerSend with the ability to add more providers in the future.

## 🏗️ Architecture Design

### Core Components

```
Authentication System
├── AuthenticationFactory (Factory Pattern)
├── BaseAuthenticationManager (Abstract Base Class)
└── MailerSendManager (Concrete Implementation)
```

### Design Principles

- **Single Responsibility**: Each manager handles only its authentication logic
- **Open/Closed**: Easy to add new providers without modifying existing code
- **Factory Pattern**: Centralized provider instantiation

## 🔧 Authentication Factory Implementation

### Factory Class Structure

```python
# src/auth/authentication_factory.py

class AuthenticationFactory:
    """
    Factory for creating authentication managers based on configuration.
    
    Currently supports MailerSend with extensibility for future providers.
    """
    
    @staticmethod
    def create_manager(provider_type="mailersend"):
        """Create authentication manager instance."""
        
    @staticmethod
    def get_available_providers():
        """Get list of available providers."""
```

## 🔌 Provider Interface

### Base Authentication Manager

```python
# src/auth/base_authentication_manager.py

from abc import ABC, abstractmethod

class BaseAuthenticationManager(ABC):
    """Abstract base class for all authentication managers."""
    
    @abstractmethod
    def authenticate(self):
        """Authenticate with the email service provider."""
        pass
        
    @abstractmethod
    def send_email(self, to_email, subject, html_content, from_email=None, from_name=None):
        """Send email using the authenticated service."""
        pass
```
    def test_connection(self) -> bool:
        """Test connection to email service."""
        pass
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name for identification."""
        pass
        
    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        pass
```

### Provider Capabilities

```python
class ProviderCapabilities:
    """Define what each provider supports."""
    
    def __init__(self):
        self.supports_templates = False
        self.supports_tracking = False
        self.supports_webhooks = False
        self.supports_bulk_send = False
        self.max_batch_size = 1
        self.rate_limit_per_minute = 60
```

## 📧 MailerSend Provider Implementation

### MailerSend Authentication

```python
# src/auth/providers/mailersend_provider.py

from mailersend import NewEmail
from src.auth.base_provider import AuthProvider
from src.config.settings import TierIISettings

class MailerSendAuthProvider(AuthProvider):
    """MailerSend authentication provider implementation."""
    
    def __init__(self, settings: TierIISettings):
        self.settings = settings
        self.api_token = settings.mailersend_api_token
        self.sender_email = settings.sender_email
        self._client = None
        
    def authenticate(self) -> bool:
        """Authenticate with MailerSend API."""
        try:
            self._client = NewEmail(self.api_token)
            return self.test_connection()
        except Exception as e:
            logger.error(f"MailerSend authentication failed: {e}")
            return False
            
    def get_client(self) -> NewEmail:
        """Get authenticated MailerSend client."""
        if not self._client:
            if not self.authenticate():
                raise AuthenticationError("Failed to authenticate with MailerSend")
        return self._client
        
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate MailerSend-specific configuration."""
        validation_results = {
            'api_token_present': bool(self.api_token),
            'api_token_format': self.api_token.startswith('ms_token_') if self.api_token else False,
            'sender_email_present': bool(self.sender_email),
            'sender_email_format': '@' in self.sender_email if self.sender_email else False
        }
        
        validation_results['is_valid'] = all(validation_results.values())
        return validation_results
        
    def test_connection(self) -> bool:
        """Test connection to MailerSend API."""
        try:
            # Attempt to get account info or send test request
            response = self._client.get_domains()  # Example API call
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"MailerSend connection test failed: {e}")
            return False
            
    @property
    def provider_name(self) -> str:
        return "mailersend"
        
    @property
    def is_configured(self) -> bool:
        """Check if MailerSend is properly configured."""
        validation = self.validate_configuration()
        return validation['is_valid']
        
    @property
    def capabilities(self) -> ProviderCapabilities:
        """MailerSend provider capabilities."""
        caps = ProviderCapabilities()
        caps.supports_templates = True
        caps.supports_tracking = True
        caps.supports_webhooks = True
        caps.supports_bulk_send = True
        caps.max_batch_size = 100
        caps.rate_limit_per_minute = 120
        return caps
```

## 🔄 Provider Selection Logic

### Automatic Provider Detection

```python
# src/auth/authentication_factory.py

class AuthenticationFactory:
    def create_authenticator(self, provider_name: str = None) -> AuthProvider:
        """
        Create authenticator with intelligent provider selection.
        
        Selection Priority:
        1. Explicitly specified provider
        2. First configured provider
        3. Default provider (MailerSend)
        4. Raise error if none available
        """
        
        # Explicit provider selection
        if provider_name:
            if provider_name not in self._providers:
                raise ValueError(f"Provider '{provider_name}' not registered")
            return self._create_provider_instance(provider_name)
            
        # Auto-detect configured providers
        configured_providers = self._get_configured_providers()
        
        if configured_providers:
            # Use first configured provider
            selected_provider = configured_providers[0]
            logger.info(f"Auto-selected provider: {selected_provider}")
            return self._create_provider_instance(selected_provider)
            
        # Fallback to default
        if self._default_provider and self._default_provider in self._providers:
            logger.warning("Using default provider as fallback")
            return self._create_provider_instance(self._default_provider)
            
        # No providers available
        raise AuthenticationError("No configured email providers available")
        
    def _get_configured_providers(self) -> List[str]:
        """Get list of properly configured providers."""
        configured = []
        
        for name, provider_class in self._providers.items():
            try:
                # Test if provider can be instantiated and configured
                instance = provider_class(load_settings())
                if instance.is_configured:
                    configured.append(name)
            except Exception as e:
                logger.debug(f"Provider {name} not configured: {e}")
                
        return configured
```

### Provider Fallback Chain

```python
class AuthenticationFactory:
    def create_with_fallback(self, preferred_providers: List[str] = None) -> AuthProvider:
        """
        Create authenticator with fallback chain.
        
        Tries providers in order until one succeeds.
        """
        
        providers_to_try = preferred_providers or self._get_configured_providers()
        
        for provider_name in providers_to_try:
            try:
                authenticator = self.create_authenticator(provider_name)
                if authenticator.test_connection():
                    logger.info(f"Successfully connected using {provider_name}")
                    return authenticator
                else:
                    logger.warning(f"Provider {provider_name} failed connection test")
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue
                
        raise AuthenticationError("All providers failed to authenticate")
```

## 🚀 Adding New Providers

### Step 1: Implement Provider Interface

```python
# src/auth/providers/google_auth.py

class GoogleAuthProvider(AuthProvider):
    """Google Workspace Gmail API provider."""
    
    def __init__(self, settings: TierIISettings):
        self.settings = settings
        self.credentials_path = settings.google_credentials_path
        self.sender_email = settings.sender_email
        self._service = None
        
    def authenticate(self) -> bool:
        """Authenticate with Google Gmail API."""
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/gmail.send']
            )
            
            self._service = build('gmail', 'v1', credentials=credentials)
            return self.test_connection()
            
        except Exception as e:
            logger.error(f"Google authentication failed: {e}")
            return False
            
    def get_client(self):
        """Get authenticated Google Gmail service."""
        if not self._service:
            if not self.authenticate():
                raise AuthenticationError("Failed to authenticate with Google")
        return self._service
        
    # ... implement other required methods
```

### Step 2: Register Provider

```python
# src/auth/__init__.py

from .authentication_factory import AuthenticationFactory
from .providers.mailersend_provider import MailerSendAuthProvider
from .providers.google_auth import GoogleAuthProvider

# Auto-register providers
factory = AuthenticationFactory()
factory.register_provider('mailersend', MailerSendAuthProvider)
factory.register_provider('google', GoogleAuthProvider)
factory.set_default_provider('mailersend')
```

### Step 3: Add Configuration Support

```python
# src/config/settings.py

class TierIISettings(BaseSettings):
    # Existing MailerSend config
    mailersend_api_token: Optional[str] = None
    
    # New Google config
    google_credentials_path: Optional[str] = None
    google_project_id: Optional[str] = None
    
    # Provider selection
    preferred_email_provider: str = "mailersend"
    
    class Config:
        env_prefix = "TIERII_"
```

## 🧪 Testing Authentication

### Unit Tests for Factory

```python
# tests/auth/test_authentication_factory.py

import pytest
from src.auth.authentication_factory import AuthenticationFactory
from src.auth.providers.mailersend_provider import MailerSendAuthProvider

class TestAuthenticationFactory:
    
    def test_provider_registration(self):
        """Test provider registration works correctly."""
        factory = AuthenticationFactory()
        factory.register_provider('test', MailerSendAuthProvider)
        
        assert 'test' in factory.get_available_providers()
        
    def test_auto_provider_selection(self, mock_settings):
        """Test automatic provider selection."""
        factory = AuthenticationFactory()
        factory.register_provider('mailersend', MailerSendAuthProvider)
        
        # Should auto-select MailerSend if configured
        authenticator = factory.create_authenticator()
        assert authenticator.provider_name == 'mailersend'
        
    def test_fallback_mechanism(self, mock_settings):
        """Test provider fallback works."""
        factory = AuthenticationFactory()
        factory.register_provider('failing', FailingProvider)
        factory.register_provider('working', WorkingProvider)
        
        # Should fallback to working provider
        authenticator = factory.create_with_fallback(['failing', 'working'])
        assert authenticator.provider_name == 'working'
```

### Integration Tests

```python
# tests/auth/test_mailersend_integration.py

class TestMailerSendIntegration:
    
    @pytest.mark.integration
    def test_mailersend_authentication(self, real_settings):
        """Test actual MailerSend authentication."""
        provider = MailerSendAuthProvider(real_settings)
        
        assert provider.is_configured
        assert provider.authenticate()
        assert provider.test_connection()
        
    @pytest.mark.integration  
    def test_end_to_end_factory(self, real_settings):
        """Test complete factory workflow."""
        factory = AuthenticationFactory()
        authenticator = factory.create_authenticator()
        
        assert authenticator.authenticate()
        client = authenticator.get_client()
        assert client is not None
```

## 🔍 Debugging Authentication

### Authentication Diagnostics

```python
# src/auth/diagnostics.py

class AuthenticationDiagnostics:
    """Diagnostic tools for authentication troubleshooting."""
    
    @staticmethod
    def run_provider_diagnostics(provider_name: str = None) -> Dict[str, Any]:
        """Run comprehensive provider diagnostics."""
        
        factory = AuthenticationFactory()
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'available_providers': factory.get_available_providers(),
            'configured_providers': factory._get_configured_providers(),
            'provider_tests': {}
        }
        
        providers_to_test = [provider_name] if provider_name else factory.get_available_providers()
        
        for name in providers_to_test:
            try:
                provider = factory.create_authenticator(name)
                
                results['provider_tests'][name] = {
                    'is_configured': provider.is_configured,
                    'configuration_validation': provider.validate_configuration(),
                    'authentication_success': provider.authenticate(),
                    'connection_test': provider.test_connection(),
                    'capabilities': provider.capabilities.__dict__
                }
                
            except Exception as e:
                results['provider_tests'][name] = {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                
        return results
```

### CLI Diagnostic Tool

```python
# scripts/auth_diagnostics.py

def main():
    """CLI tool for authentication diagnostics."""
    import argparse
    
    parser = argparse.ArgumentParser(description='TierII Authentication Diagnostics')
    parser.add_argument('--provider', help='Test specific provider')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    diagnostics = AuthenticationDiagnostics()
    results = diagnostics.run_provider_diagnostics(args.provider)
    
    if args.verbose:
        print(json.dumps(results, indent=2))
    else:
        # Summary output
        print(f"Available providers: {', '.join(results['available_providers'])}")
        print(f"Configured providers: {', '.join(results['configured_providers'])}")
        
        for name, test_results in results['provider_tests'].items():
            if 'error' in test_results:
                print(f"❌ {name}: {test_results['error']}")
            else:
                status = "✅" if test_results['connection_test'] else "❌"
                print(f"{status} {name}: {'Connected' if test_results['connection_test'] else 'Failed'}")

if __name__ == '__main__':
    main()
```

## 📚 Usage Examples

### Basic Usage

```python
# Simple authentication
from src.auth.authentication_factory import AuthenticationFactory

factory = AuthenticationFactory()
authenticator = factory.create_authenticator()  # Auto-selects best provider

if authenticator.authenticate():
    client = authenticator.get_client()
    # Use client for sending emails
```

### Advanced Usage with Fallback

```python
# Multi-provider fallback
preferred_providers = ['google', 'mailersend', 'smtp']
authenticator = factory.create_with_fallback(preferred_providers)

# Provider-specific configuration
if authenticator.provider_name == 'mailersend':
    # MailerSend-specific optimizations
    batch_size = authenticator.capabilities.max_batch_size
elif authenticator.provider_name == 'google':
    # Google-specific handling
    batch_size = 50  # Conservative for Gmail API
```

### Configuration-Driven Selection

```python
# Environment-based provider selection
import os

provider_name = os.getenv('TIERII_EMAIL_PROVIDER', 'mailersend')
authenticator = factory.create_authenticator(provider_name)
```

## 🚨 Troubleshooting

### Common Issues

#### Provider Not Found
```
Error: Provider 'xyz' not registered
Solution: Check provider is imported and registered in factory
```

#### Authentication Failed
```
Error: Failed to authenticate with MailerSend
Solution: Verify API token and network connectivity
```

#### No Configured Providers
```
Error: No configured email providers available
Solution: Set required environment variables for at least one provider
```

### Debug Mode

```python
# Enable debug logging for authentication
import logging
logging.getLogger('src.auth').setLevel(logging.DEBUG)

# Run diagnostics
from src.auth.diagnostics import AuthenticationDiagnostics
results = AuthenticationDiagnostics.run_provider_diagnostics()
print(json.dumps(results, indent=2))
```

## 📚 Related Documentation

- **[Configuration Reference](configuration.md)** - Environment variables and settings
- **[MailerSend Setup](mailersend.md)** - MailerSend-specific configuration
- **[Development Guide](../guides/development.md)** - Adding new providers
- **[Testing Guide](../guides/testing.md)** - Authentication testing strategies

---

**Authentication Version**: 0.1.0  
**Pattern**: Factory Pattern with Provider Interface  
**Extensibility**: Designed for multiple email service providers