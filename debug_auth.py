#!/usr/bin/env python3
"""Debug script to test authentication manager creation."""

import sys
import os
sys.path.append('src')

# Test settings loading
try:
    from src.config.settings import TierIISettings
    settings = TierIISettings()
    print(f"✓ Settings loaded successfully")
    print(f"  - sender_email: {settings.sender_email}")
    print(f"  - tenant_id: {settings.tenant_id}")
    print(f"  - client_id: {settings.client_id}")
    print(f"  - client_secret: {'***' if settings.client_secret else None}")
    print(f"  - smtp_server: {settings.smtp_server}")
    print(f"  - smtp_port: {settings.smtp_port}")
except Exception as e:
    print(f"✗ Settings loading failed: {e}")
    settings = None

# Test authentication factory
try:
    from src.auth.authentication_factory import authentication_factory
    from src.auth.base_authentication_manager import AuthenticationProvider
    print(f"✓ Authentication factory imported")
except Exception as e:
    print(f"✗ Authentication factory import failed: {e}")
    sys.exit(1)

# Test authentication manager creation
try:
    if settings:
        config = {
            "tenant_id": getattr(settings, 'tenant_id', None),
            "client_id": getattr(settings, 'client_id', None),
            "client_secret": getattr(settings, 'client_secret', None),
            "sender_email": getattr(settings, 'sender_email', None),
            "smtp_server": getattr(settings, 'smtp_server', None),
            "smtp_port": getattr(settings, 'smtp_port', None),
        }
        
        print(f"\nConfig for authentication:")
        for key, value in config.items():
            if key == 'client_secret':
                print(f"  - {key}: {'***' if value else None}")
            else:
                print(f"  - {key}: {value}")
        
        # Test Microsoft OAuth manager creation
        print(f"\nTesting Microsoft OAuth manager creation...")
        manager = authentication_factory.create_with_fallback(
            primary_provider=AuthenticationProvider.MICROSOFT_OAUTH,
            fallback_providers=[AuthenticationProvider.GMAIL_APP_PASSWORD],
            config=config
        )
        print(f"✓ Authentication manager created: {manager.provider.name}")
        
        # Test authentication
        print(f"\nTesting authentication...")
        auth_result = manager.authenticate(config)
        print(f"Authentication result: {auth_result}")
        
except Exception as e:
    print(f"✗ Authentication manager creation failed: {e}")
    import traceback
    traceback.print_exc()