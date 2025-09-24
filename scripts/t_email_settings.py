#!/usr/bin/env python3
"""
Test MailerSend Configuration

This script tests the MailerSend API configuration and validates
that all required settings are properly configured.
"""

import sys
from datetime import datetime

# Import configuration
try:
    from src.config.settings import load_settings
    settings = load_settings()
except ImportError as e:
    print(
        f"Error: Could not import settings: {e}. Please ensure src.config.settings is available."
    )
    sys.exit(1)
except Exception as e:
    print(
        f"Error: Could not load configuration: {e}. Please check your environment variables."
    )
    sys.exit(1)


def test_mailersend_config():
    """Test MailerSend configuration"""
    try:
        print("\n--- Testing MailerSend Configuration ---")
        
        # Check required settings
        print(f"Sender Email: {settings.sender_email}")
        print(f"Sender Name: {settings.sender_name}")
        print(f"API Token: {'*' * 20}...{settings.mailersend_api_token[-4:] if len(settings.mailersend_api_token) > 4 else '****'}")
        
        # Check campaign settings
        print(f"Batch Size: {settings.campaign_batch_size}")
        print(f"Delay Minutes: {settings.campaign_delay_minutes}")
        
        # Check test settings
        if settings.test_recipient_email:
            print(f"Test Recipient: {settings.test_recipient_email}")
        
        print("✅ SUCCESS: MailerSend configuration loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: MailerSend configuration error: {e}")
        return False


def test_authentication_manager():
    """Test MailerSend authentication manager creation"""
    try:
        print("\n--- Testing Authentication Manager ---")
        
        from src.email_campaign import create_authentication_manager
        
        manager = create_authentication_manager()
        print(f"Manager created: {type(manager).__name__}")
        print(f"Provider: {manager.provider}")
        
        print("✅ SUCCESS: Authentication manager created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Authentication manager error: {e}")
        return False


def test_email_sending():
    """Test email sending functionality (dry run)"""
    try:
        print("\n--- Testing Email Sending (Dry Run) ---")
        
        from src.email_campaign import send_email
        from unittest.mock import patch, Mock
        
        # Mock the authentication manager for testing
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        
        with patch('src.email_campaign.auth_manager', mock_manager):
            result = send_email("test@example.com", "Test User")
            
        if result:
            print("✅ SUCCESS: Email sending function works correctly!")
            return True
        else:
            print("❌ FAILED: Email sending function returned False")
            return False
        
    except Exception as e:
        print(f"❌ FAILED: Email sending error: {e}")
        return False


def main():
    """Run all MailerSend configuration tests"""
    print("=" * 60)
    print("MAILERSEND CONFIGURATION TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Configuration Loading", test_mailersend_config),
        ("Authentication Manager", test_authentication_manager),
        ("Email Sending", test_email_sending),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ FAILED: Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MailerSend configuration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check your MailerSend configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
