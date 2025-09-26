"""Authentication cache manager for optimizing authentication manager lifecycle.

This module provides centralized caching for authentication managers to prevent
redundant creation and improve system performance by reusing authenticated instances.
"""

import threading
import weakref
from typing import Dict, Optional, Any, ClassVar
from datetime import datetime, timedelta
import logging

from .base_authentication_manager import AuthenticationProvider, BaseAuthenticationManager


class AuthenticationCache:
    """Centralized cache for authentication managers.
    
    Implements singleton pattern with weak references to prevent memory leaks
    while maintaining performance benefits of caching authenticated managers.
    """
    
    _instance: ClassVar[Optional['AuthenticationCache']] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()
    
    def __new__(cls) -> 'AuthenticationCache':
        """Ensure singleton pattern for cache instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize authentication cache."""
        if hasattr(self, '_initialized'):
            return
            
        self._cache: Dict[str, weakref.ReferenceType] = {}
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._initialized = True
    
    def _generate_cache_key(self, provider: AuthenticationProvider, config: Dict[str, Any]) -> str:
        """Generate cache key for authentication manager.
        
        Args:
            provider: Authentication provider type
            config: Configuration dictionary
            
        Returns:
            str: Unique cache key
        """
        # Create key based on provider and critical config elements
        key_parts = [provider.value]
        
        # Add relevant config elements for key generation
        if 'mailersend_api_token' in config:
            # Use first 16 chars of API token for security
            key_parts.append(f"token_{config['mailersend_api_token'][:16]}")
        elif 'api_token' in config:
            # Use first 16 chars of API token for security (generic key)
            key_parts.append(f"token_{config['api_token'][:16]}")
        if 'sender_email' in config:
            key_parts.append(f"sender_{config['sender_email']}")
            
        return "_".join(key_parts)
    
    def get_manager(self, provider: AuthenticationProvider, config: Dict[str, Any]) -> Optional[BaseAuthenticationManager]:
        """Retrieve cached authentication manager if available.
        
        Args:
            provider: Authentication provider type
            config: Configuration dictionary
            
        Returns:
            BaseAuthenticationManager or None if not cached or expired
        """
        cache_key = self._generate_cache_key(provider, config)
        
        with self._cache_lock:
            if cache_key not in self._cache:
                return None
                
            # Check if weak reference is still valid
            manager_ref = self._cache[cache_key]
            manager = manager_ref()
            
            if manager is None:
                # Clean up dead reference
                self._cleanup_cache_entry(cache_key)
                return None
            
            # Check if manager is still valid and authenticated
            metadata = self._cache_metadata.get(cache_key, {})
            cache_time = metadata.get('cached_at')
            max_age = metadata.get('max_age_minutes', 60)  # Default 1 hour
            
            if cache_time and datetime.now() - cache_time > timedelta(minutes=max_age):
                self._logger.debug(f"Cache entry expired for key: {cache_key[:16]}...")
                self._cleanup_cache_entry(cache_key)
                return None
            
            # Verify manager is still authenticated
            print(f"DEBUG: get_manager - manager.is_authenticated: {manager.is_authenticated}")
            if not manager.is_authenticated:
                self._logger.debug(f"Cached manager no longer authenticated for key: {cache_key[:16]}...")
                self._cleanup_cache_entry(cache_key)
                return None
            
            self._logger.debug(f"Retrieved cached authentication manager for key: {cache_key[:16]}...")
            return manager
    
    def cache_manager(self, provider: AuthenticationProvider, config: Dict[str, Any], 
                     manager: BaseAuthenticationManager, max_age_minutes: int = 60) -> None:
        """Cache an authentication manager.
        
        Args:
            provider: Authentication provider type
            config: Configuration dictionary
            manager: Authentication manager to cache
            max_age_minutes: Maximum age in minutes before cache expires
        """
        cache_key = self._generate_cache_key(provider, config)
        print(f"DEBUG: cache_manager called with provider={provider.value}, cache_key={cache_key[:16]}...")
        
        with self._cache_lock:
            # Create weak reference to prevent memory leaks
            manager_ref = weakref.ref(manager, lambda ref: self._cleanup_cache_entry(cache_key))
            
            self._cache[cache_key] = manager_ref
            self._cache_metadata[cache_key] = {
                'cached_at': datetime.now(),
                'max_age_minutes': max_age_minutes,
                'provider': provider.value,
                'authenticated': manager.is_authenticated
            }
            
            print(f"DEBUG: Manager cached successfully. Cache size: {len(self._cache)}")
            self._logger.debug(f"Cached authentication manager for key: {cache_key[:16]}...")
    
    def _cleanup_cache_entry(self, cache_key: str) -> None:
        """Clean up a cache entry and its metadata.
        
        Args:
            cache_key: Cache key to clean up
        """
        with self._cache_lock:
            self._cache.pop(cache_key, None)
            self._cache_metadata.pop(cache_key, None)
            self._logger.debug(f"Cleaned up cache entry: {cache_key[:16]}...")
    
    def invalidate_cache(self, provider: Optional[AuthenticationProvider] = None) -> None:
        """Invalidate cache entries.
        
        Args:
            provider: If specified, only invalidate entries for this provider.
                     If None, invalidate all entries.
        """
        with self._cache_lock:
            if provider is None:
                # Clear all cache entries
                keys_to_remove = list(self._cache.keys())
                for key in keys_to_remove:
                    self._cleanup_cache_entry(key)
                self._logger.info("Invalidated all authentication cache entries")
            else:
                # Clear entries for specific provider
                keys_to_remove = [
                    key for key, metadata in self._cache_metadata.items()
                    if metadata.get('provider') == provider.value
                ]
                for key in keys_to_remove:
                    self._cleanup_cache_entry(key)
                self._logger.info(f"Invalidated cache entries for provider: {provider.value}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict containing cache statistics
        """
        with self._cache_lock:
            active_entries = sum(1 for ref in self._cache.values() if ref() is not None)
            print(f"DEBUG: get_cache_stats - cache size: {len(self._cache)}, metadata size: {len(self._cache_metadata)}")
            print(f"DEBUG: cache keys: {list(self._cache.keys())}")
            print(f"DEBUG: metadata keys: {list(self._cache_metadata.keys())}")
            
            return {
                'total_entries': len(self._cache),
                'active_entries': active_entries,
                'dead_references': len(self._cache) - active_entries,
                'providers': list(set(
                    metadata.get('provider') 
                    for metadata in self._cache_metadata.values()
                    if metadata.get('provider')
                ))
            }
    
    def cleanup_dead_references(self) -> int:
        """Clean up dead weak references.
        
        Returns:
            int: Number of dead references cleaned up
        """
        with self._cache_lock:
            dead_keys = [
                key for key, ref in self._cache.items()
                if ref() is None
            ]
            
            for key in dead_keys:
                self._cleanup_cache_entry(key)
            
            if dead_keys:
                self._logger.debug(f"Cleaned up {len(dead_keys)} dead cache references")
            
            return len(dead_keys)


# Global cache instance
authentication_cache = AuthenticationCache()