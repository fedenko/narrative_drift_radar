"""
LLM response caching utilities using Redis for cost optimization.
"""
import json
import hashlib
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.conf import settings


class LLMCache:
    """
    Cache for LLM responses to avoid duplicate API calls.
    Uses Django's cache framework (can be Redis, Memcached, etc.)
    """
    
    def __init__(self, default_timeout: int = 86400 * 7):  # 7 days default
        self.default_timeout = default_timeout
        self.cache_prefix = "llm_cache"
    
    def _make_cache_key(self, content_hash: str, task_type: str) -> str:
        """Create cache key from content hash and task type."""
        return f"{self.cache_prefix}:{task_type}:{content_hash}"
    
    def _hash_content(self, content: str) -> str:
        """Create hash from content for caching."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get_cached_response(self, content: str, task_type: str = "naming") -> Optional[Dict[str, Any]]:
        """
        Get cached LLM response if available.
        
        Args:
            content: Input content that was sent to LLM
            task_type: Type of task ('naming', 'brief', etc.)
            
        Returns:
            Cached response dict or None if not found
        """
        try:
            content_hash = self._hash_content(content)
            cache_key = self._make_cache_key(content_hash, task_type)
            
            cached_data = cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data) if isinstance(cached_data, str) else cached_data
                
        except Exception as e:
            # Log error but don't fail
            print(f"Cache read error: {e}")
        
        return None
    
    def cache_response(self, content: str, response: str, task_type: str = "naming", 
                      metadata: Optional[Dict[str, Any]] = None, 
                      timeout: Optional[int] = None) -> bool:
        """
        Cache LLM response.
        
        Args:
            content: Input content that was sent to LLM
            response: LLM response to cache
            task_type: Type of task ('naming', 'brief', etc.)
            metadata: Optional metadata (cost, model, etc.)
            timeout: Cache timeout in seconds
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            content_hash = self._hash_content(content)
            cache_key = self._make_cache_key(content_hash, task_type)
            
            cache_data = {
                'response': response,
                'content_hash': content_hash,
                'task_type': task_type,
                'metadata': metadata or {}
            }
            
            cache_timeout = timeout or self.default_timeout
            cache.set(cache_key, json.dumps(cache_data), cache_timeout)
            
            return True
            
        except Exception as e:
            # Log error but don't fail
            print(f"Cache write error: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get basic cache statistics."""
        # This is implementation-dependent and might not work with all cache backends
        try:
            if hasattr(cache, '_cache') and hasattr(cache._cache, 'info'):
                return cache._cache.info()
        except:
            pass
        
        return {"status": "Cache stats not available"}
    
    def clear_cache(self, task_type: Optional[str] = None) -> bool:
        """
        Clear cache entries.
        
        Args:
            task_type: If specified, only clear entries for this task type
            
        Returns:
            True if successful
        """
        try:
            if task_type:
                # This is a simplified implementation
                # In production, you might want to use cache patterns
                # or maintain a separate index of cache keys
                pass
            else:
                cache.clear()
            
            return True
            
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False


# Global cache instance
llm_cache = LLMCache()


def get_cached_llm_response(content: str, task_type: str = "naming") -> Optional[str]:
    """
    Convenience function to get cached LLM response.
    
    Args:
        content: Content that was sent to LLM
        task_type: Task type
        
    Returns:
        Cached response string or None
    """
    cached_data = llm_cache.get_cached_response(content, task_type)
    if cached_data:
        return cached_data.get('response')
    return None


def cache_llm_response(content: str, response: str, task_type: str = "naming", 
                      cost: float = 0.0) -> bool:
    """
    Convenience function to cache LLM response.
    
    Args:
        content: Content that was sent to LLM
        response: LLM response
        task_type: Task type
        cost: API call cost for tracking
        
    Returns:
        True if cached successfully
    """
    metadata = {
        'cost': cost,
        'cached_at': timezone.now().isoformat() if 'timezone' in globals() else None
    }
    
    return llm_cache.cache_response(content, response, task_type, metadata)


# Example usage functions for the clustering command
def get_cluster_name_cached(compressed_content: Dict[str, Any], llm_func) -> str:
    """
    Get cluster name with caching.
    
    Args:
        compressed_content: Compressed content dict
        llm_func: Function that calls LLM to generate name
        
    Returns:
        Generated or cached cluster name
    """
    from narratives.utils.content_compression import ContentCompressor
    
    compressor = ContentCompressor()
    prompt_content = compressor.create_llm_prompt_content(compressed_content)
    
    # Try cache first
    cached_response = get_cached_llm_response(prompt_content, "naming")
    if cached_response:
        return cached_response
    
    # Generate new response
    response = llm_func(prompt_content)
    
    # Cache the response
    cache_llm_response(prompt_content, response, "naming", 0.0001)
    
    return response


def get_weekly_brief_cached(narratives_summary: str, llm_func) -> str:
    """
    Get weekly brief with caching.
    
    Args:
        narratives_summary: Summary of week's narratives
        llm_func: Function that calls LLM to generate brief
        
    Returns:
        Generated or cached weekly brief
    """
    # Try cache first
    cached_response = get_cached_llm_response(narratives_summary, "brief")
    if cached_response:
        return cached_response
    
    # Generate new response
    response = llm_func(narratives_summary)
    
    # Cache the response
    cache_llm_response(narratives_summary, response, "brief", 0.001)
    
    return response