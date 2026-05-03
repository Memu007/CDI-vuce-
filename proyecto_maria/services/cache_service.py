"""
Redis cache service for MARIA project
"""

import redis.asyncio as redis
import json
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta
import hashlib

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.enabled = os.getenv("ENABLE_REDIS", "false").lower() == "true"
        self._client = None
        
    async def get_client(self):
        """Get Redis client (lazy initialization)"""
        if not self.enabled:
            return None
            
        if self._client is None:
            try:
                self._client = redis.from_url(self.redis_url, decode_responses=True)
                await self._client.ping()
                logger.info("✅ Redis client connected")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                self._client = None
                
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        client = await self.get_client()
        if not client:
            return None
            
        try:
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"❌ Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache with TTL"""
        client = await self.get_client()
        if not client:
            return False
            
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            await client.setex(key, ttl_seconds, serialized)
            return True
        except Exception as e:
            logger.error(f"❌ Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        client = await self.get_client()
        if not client:
            return False
            
        try:
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"❌ Cache delete error for key {key}: {e}")
            return False
    
    async def get_or_set(self, key: str, factory_func, ttl_seconds: int = 3600) -> Any:
        """Get from cache or compute and cache"""
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Compute value
        try:
            if callable(factory_func):
                value = await factory_func() if hasattr(factory_func, '__call__') else factory_func
            else:
                value = factory_func
            
            # Cache the result
            await self.set(key, value, ttl_seconds)
            return value
        except Exception as e:
            logger.error(f"❌ Cache factory error for key {key}: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        if not self.enabled:
            return {"status": "disabled", "connected": False}
            
        client = await self.get_client()
        if not client:
            return {"status": "error", "connected": False}
            
        try:
            await client.ping()
            info = await client.info()
            return {
                "status": "healthy",
                "connected": True,
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients")
            }
        except Exception as e:
            return {"status": "error", "connected": False, "error": str(e)}

# Specialized cache services

class NCMCacheService(CacheService):
    """Specialized cache for NCM data"""
    
    async def get_ncm_data(self, ncm_code: str) -> Optional[Dict[str, Any]]:
        """Get NCM data from cache"""
        key = f"ncm:{ncm_code}"
        return await self.get(key)
    
    async def cache_ncm_data(self, ncm_code: str, data: Dict[str, Any], ttl_hours: int = 24):
        """Cache NCM data"""
        key = f"ncm:{ncm_code}"
        return await self.set(key, data, ttl_hours * 3600)
    
    async def get_ncm_search_results(self, query: str, limit: int = 10) -> Optional[List[Dict]]:
        """Get NCM search results from cache"""
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:8]
        key = f"ncm_search:{query_hash}:{limit}"
        return await self.get(key)
    
    async def cache_ncm_search_results(self, query: str, results: List[Dict], limit: int = 10, ttl_hours: int = 6):
        """Cache NCM search results"""
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:8]
        key = f"ncm_search:{query_hash}:{limit}"
        return await self.set(key, results, ttl_hours * 3600)

class LLMCacheService(CacheService):
    """Specialized cache for LLM results"""
    
    async def get_pdf_extraction(self, pdf_hash: str) -> Optional[Dict[str, Any]]:
        """Get PDF extraction result from cache"""
        key = f"llm_pdf:{pdf_hash}"
        return await self.get(key)
    
    async def cache_pdf_extraction(self, pdf_hash: str, result: Dict[str, Any], ttl_hours: int = 72):
        """Cache PDF extraction result"""
        key = f"llm_pdf:{pdf_hash}"
        return await self.set(key, result, ttl_hours * 3600)
    
    async def get_item_enrichment(self, item_hash: str) -> Optional[Dict[str, Any]]:
        """Get item enrichment result from cache"""
        key = f"llm_enrich:{item_hash}"
        return await self.get(key)
    
    async def cache_item_enrichment(self, item_hash: str, result: Dict[str, Any], ttl_hours: int = 24):
        """Cache item enrichment result"""
        key = f"llm_enrich:{item_hash}"
        return await self.set(key, result, ttl_hours * 3600)

class VUCECacheService(CacheService):
    """Specialized cache for VUCE API calls"""
    
    async def get_vuce_ncm(self, ncm_code: str) -> Optional[Dict[str, Any]]:
        """Get VUCE NCM data from cache"""
        key = f"vuce_ncm:{ncm_code}"
        return await self.get(key)
    
    async def cache_vuce_ncm(self, ncm_code: str, data: Dict[str, Any], ttl_hours: int = 168):  # 1 week
        """Cache VUCE NCM data"""
        key = f"vuce_ncm:{ncm_code}"
        return await self.set(key, data, ttl_hours * 3600)

# Global instances
cache_service = CacheService()
ncm_cache = NCMCacheService()
llm_cache = LLMCacheService()
vuce_cache = VUCECacheService()
