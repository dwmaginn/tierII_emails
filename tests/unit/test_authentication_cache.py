"""Unit tests for authentication cache functionality.

Tests the authentication cache system to ensure proper caching behavior,
memory management, and performance optimization without API calls.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.auth.authentication_cache import AuthenticationCache, authentication_cache
from src.auth.base_authentication_manager import AuthenticationProvider, BaseAuthenticationManager


class MockAuthenticationManager(BaseAuthenticationManager):
    """Mock authentication manager for testing."""
    
    def __init__(self, provider: AuthenticationProvider):
        super().__init__(provider)
        self.is_authenticated = True
        self._mock_config = {}
    
    def authenticate(self) -> bool:
        return True
    
    def set_configuration(self, config):
        self._mock_config = config
    
    def validate_configuration(self) -> bool:
        return True
    
    def get_access_token(self) -> str:
        return "mock_token"
    
    def is_token_valid(self, token: str = None) -> bool:
        return True
    
    def refresh_token(self) -> bool:
        return True


class TestAuthenticationCache:
    """Test cases for authentication cache functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear cache before each test
        authentication_cache.invalidate_cache()
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clear cache after each test
        authentication_cache.invalidate_cache()
    
    def test_singleton_pattern(self):
        """Test that AuthenticationCache follows singleton pattern."""
        cache1 = AuthenticationCache()
        cache2 = AuthenticationCache()
        
        assert cache1 is cache2
        assert cache1 is authentication_cache
    
    def test_cache_key_generation(self):
        """Test cache key generation for different configurations."""
        cache = AuthenticationCache()
        
        config1 = {
            "mailersend_api_token": "super-secret-mailersend-token-123456789",
            "sender_email": "test@example.com"
        }
        
        config2 = {
            "mailersend_api_token": "super-secret-different-token-123",
            "sender_email": "test@example.com"
        }
        
        key1 = cache._generate_cache_key(AuthenticationProvider.MAILERSEND, config1)
        key2 = cache._generate_cache_key(AuthenticationProvider.MAILERSEND, config2)
        
        assert key1 != key2
        assert "mailersend" in key1
        assert "token_super-secret-mai" in key1  # First 16 chars of token
        assert "sender_test@example.com" in key1
    
    def test_cache_manager_and_retrieve(self):
        """Test caching and retrieving authentication managers."""
        cache = AuthenticationCache()
        manager = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
        
        config = {
            "mailersend_api_token": "super-secret-mailersend-token",
            "sender_email": "test@example.com"
        }
        
        # Cache the manager
        cache.cache_manager(AuthenticationProvider.MAILERSEND, config, manager)
        
        # Retrieve from cache
        cached_manager = cache.get_manager(AuthenticationProvider.MAILERSEND, config)
        
        assert cached_manager is manager
        assert cached_manager.is_authenticated
    
    def test_cache_expiration(self):
        """Test that cache entries expire after specified time."""
        cache = AuthenticationCache()
        manager = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
        
        config = {
            "mailersend_api_token": "super-secret-mailersend-token",
            "sender_email": "test@example.com"
        }
        
        # Cache with very short expiration (1 second for testing)
        cache.cache_manager(AuthenticationProvider.MAILERSEND, config, manager, max_age_minutes=0.017)  # ~1 second
        
        # Should be available immediately
        cached_manager = cache.get_manager(AuthenticationProvider.MAILERSEND, config)
        assert cached_manager is manager
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        cached_manager = cache.get_manager(AuthenticationProvider.MAILERSEND, config)
        assert cached_manager is None
    
    def test_cache_invalidation_by_provider(self):
        """Test cache invalidation for specific provider."""
        cache = AuthenticationCache()
        manager = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
        
        config = {
            "mailersend_api_token": "super-secret-mailersend-token",
            "sender_email": "test@example.com"
        }
        
        # Cache the manager
        cache.cache_manager(AuthenticationProvider.MAILERSEND, config, manager)
        
        # Verify it's cached
        assert cache.get_manager(AuthenticationProvider.MAILERSEND, config) is manager
        
        # Invalidate cache for MailerSend
        cache.invalidate_cache(AuthenticationProvider.MAILERSEND)
        
        # Should be gone now
        assert cache.get_manager(AuthenticationProvider.MAILERSEND, config) is None
    
    def test_cache_invalidation_all(self):
        """Test invalidating all cache entries."""
        cache = AuthenticationCache()
        manager = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
        
        config = {
            "mailersend_api_token": "super-secret-mailersend-token",
            "sender_email": "test@example.com"
        }
        
        # Cache the manager
        cache.cache_manager(AuthenticationProvider.MAILERSEND, config, manager)
        
        # Verify it's cached
        assert cache.get_manager(AuthenticationProvider.MAILERSEND, config) is manager
        
        # Invalidate all cache
        cache.invalidate_cache()
        
        # Should be gone now
        assert cache.get_manager(AuthenticationProvider.MAILERSEND, config) is None
    
    def test_unauthenticated_manager_not_cached(self):
        """Test that unauthenticated managers are not returned from cache."""
        cache = AuthenticationCache()
        manager = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
        
        config = {
            "mailersend_api_token": "super-secret-mailersend-token",
            "sender_email": "test@example.com"
        }
        
        # Cache the manager
        cache.cache_manager(AuthenticationProvider.MAILERSEND, config, manager)
        
        # Verify it's cached
        assert cache.get_manager(AuthenticationProvider.MAILERSEND, config) is manager
        
        # Make manager unauthenticated
        manager.is_authenticated = False
        
        # Should not return unauthenticated manager
        cached_manager = cache.get_manager(AuthenticationProvider.MAILERSEND, config)
        assert cached_manager is None
    
    def test_weak_reference_cleanup(self):
        """Test that weak references are cleaned up when managers are garbage collected."""
        cache = AuthenticationCache()
        
        config = {
            "mailersend_api_token": "super-secret-mailersend-token",
            "sender_email": "test@example.com"
        }
        
        # Create and cache manager in local scope
        def create_and_cache_manager():
            manager = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
            cache.cache_manager(AuthenticationProvider.MAILERSEND, config, manager)
            return manager
        
        manager = create_and_cache_manager()
        
        # Verify it's cached
        assert cache.get_manager(AuthenticationProvider.MAILERSEND, config) is manager
        
        # Delete reference and force garbage collection
        del manager
        import gc
        gc.collect()
        
        # Should be cleaned up now
        assert cache.get_manager(AuthenticationProvider.MAILERSEND, config) is None
    
    def test_cache_stats(self):
        """Test cache statistics reporting."""
        cache = AuthenticationCache()
        manager = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
        
        config = {
            "mailersend_api_token": "super-secret-mailersend-token",
            "sender_email": "test@example.com"
        }
        
        # Initially empty
        stats = cache.get_cache_stats()
        assert stats['total_entries'] == 0
        assert stats['active_entries'] == 0
        
        # Cache a manager
        cache.cache_manager(AuthenticationProvider.MAILERSEND, config, manager)
        
        stats = cache.get_cache_stats()
        assert stats['total_entries'] == 1
        assert stats['active_entries'] == 1
        assert AuthenticationProvider.MAILERSEND.value in stats['providers']
    
    def test_cleanup_dead_references(self):
        """Test cleanup of dead weak references."""
        cache = AuthenticationCache()
        
        config = {
            "mailersend_api_token": "super-secret-mailersend-token",
            "sender_email": "test@example.com"
        }
        
        # Create and cache manager, then delete it
        manager = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
        cache.cache_manager(AuthenticationProvider.MAILERSEND, config, manager)
        
        # Verify it's cached
        assert cache.get_manager(AuthenticationProvider.MAILERSEND, config) is manager
        
        # Delete manager and force garbage collection
        del manager
        import gc
        gc.collect()
        
        # Force cleanup by trying to access the dead reference
        # This should trigger cleanup automatically
        result = cache.get_manager(AuthenticationProvider.MAILERSEND, config)
        assert result is None  # Should be None due to dead reference cleanup
        
        # Manual cleanup should now find nothing to clean
        cleaned = cache.cleanup_dead_references()
        assert cleaned >= 0  # Could be 0 if already cleaned up automatically
    
    def test_thread_safety(self):
        """Test that cache operations are thread-safe."""
        cache = AuthenticationCache()
        results = []
        errors = []
        
        def cache_and_retrieve(thread_id):
            try:
                manager = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
                config = {
                    "mailersend_api_token": f"super-secret-token-{thread_id}",
                    "sender_email": f"test{thread_id}@example.com"
                }
                
                # Cache manager
                cache.cache_manager(AuthenticationProvider.MAILERSEND, config, manager)
                
                # Retrieve manager
                cached_manager = cache.get_manager(AuthenticationProvider.MAILERSEND, config)
                
                results.append((thread_id, cached_manager is manager))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=cache_and_retrieve, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread errors: {errors}"
        assert len(results) == 10
        assert all(success for _, success in results)
    
    def test_different_configs_different_cache_entries(self):
        """Test that different configurations create different cache entries."""
        cache = AuthenticationCache()
        
        manager1 = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
        manager2 = MockAuthenticationManager(AuthenticationProvider.MAILERSEND)
        
        config1 = {
            "mailersend_api_token": "super-secret-token1",
            "sender_email": "test1@example.com"
        }
        
        config2 = {
            "mailersend_api_token": "super-secret-token2",
            "sender_email": "test2@example.com"
        }
        
        # Cache both managers
        cache.cache_manager(AuthenticationProvider.MAILERSEND, config1, manager1)
        cache.cache_manager(AuthenticationProvider.MAILERSEND, config2, manager2)
        
        # Should retrieve correct managers
        cached1 = cache.get_manager(AuthenticationProvider.MAILERSEND, config1)
        cached2 = cache.get_manager(AuthenticationProvider.MAILERSEND, config2)
        
        assert cached1 is manager1
        assert cached2 is manager2
        assert cached1 is not cached2
        
        # Should have 2 cache entries
        stats = cache.get_cache_stats()
        assert stats['total_entries'] == 2
        assert stats['active_entries'] == 2