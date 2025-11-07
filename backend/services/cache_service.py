"""
Redis Cache Service - Sistema di Caching Distribuito per Tutor AI
Implementazione completa con cache layering, invalidazione intelligente e monitoring
"""

import redis
import json
import pickle
import hashlib
import time
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
from enum import Enum
import asyncio
from functools import wraps
import numpy as np

logger = structlog.get_logger()

class CacheType(Enum):
    """Tipi di cache supportati"""
    QUERY_RESULT = "query_result"
    EMBEDDING = "embedding"
    SESSION = "session"
    RATE_LIMIT = "rate_limit"
    DOCUMENT = "document"
    HYBRAR_SEARCH = "hybrid_search"
    LLM_RESPONSE = "llm_response"

@dataclass
class CacheConfig:
    """Configurazione per una cache entry"""
    ttl: int  # Time to live in seconds
    max_size: Optional[int] = None
    version: str = "1.0"
    compression: bool = True

class RedisCacheService:
    """
    Servizio di caching Redis con funzionalità avanzate:
    - Cache layering (multi-level)
    - Intelligent invalidation
    - Compression and serialization
    - Metrics and monitoring
    - Fallback strategies
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 0):
        self.redis_url = redis_url
        self.db = db
        self.redis_client = None
        self.connection_pool = None

        # Configurazioni TTL per tipo di cache (in secondi)
        self.cache_configs = {
            CacheType.QUERY_RESULT: CacheConfig(ttl=3600),  # 1 ora
            CacheType.EMBEDDING: CacheConfig(ttl=86400),    # 24 ore
            CacheType.SESSION: CacheConfig(ttl=1800),       # 30 minuti
            CacheType.RATE_LIMIT: CacheConfig(ttl=60),      # 1 minuto
            CacheType.DOCUMENT: CacheConfig(ttl=7200),      # 2 ore
            CacheType.HYBRAR_SEARCH: CacheConfig(ttl=1800), # 30 minuti
            CacheType.LLM_RESPONSE: CacheConfig(ttl=900),   # 15 minuti
        }

        # Metrics tracking
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
            "compression_ratio": 0.0,
            "avg_response_time": 0.0
        }

        self._initialize_connection()

    def _initialize_connection(self):
        """Inizializza la connessione Redis con retry logic"""
        try:
            self.connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                db=self.db,
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)

            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully",
                       redis_url=self.redis_url, db=self.db)

        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            self.redis_client = None

    def _generate_cache_key(self, cache_type: CacheType, identifier: str,
                          additional_params: Optional[Dict] = None) -> str:
        """
        Genera cache key con hashing per consistenza
        """
        base_key = f"tutor_ai:{cache_type.value}:{identifier}"

        if additional_params:
            # Sort params for consistent hashing
            sorted_params = json.dumps(additional_params, sort_keys=True)
            param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
            base_key += f":{param_hash}"

        return base_key

    def _serialize_data(self, data: Any, config: CacheConfig) -> bytes:
        """
        Serializza i dati con compressione opzionale
        """
        try:
            if config.compression:
                # Use pickle for numpy arrays and complex objects
                serialized = pickle.dumps(data)
                # Could add compression here if needed
                return serialized
            else:
                # Use JSON for simple data structures
                if isinstance(data, (dict, list, str, int, float, bool)):
                    return json.dumps(data).encode('utf-8')
                else:
                    return pickle.dumps(data)
        except Exception as e:
            logger.error("Error serializing cache data", error=str(e))
            raise

    def _deserialize_data(self, data: bytes, config: CacheConfig) -> Any:
        """
        Deserializza i dati dal formato cache
        """
        try:
            if config.compression or not isinstance(data, (str, bytes)):
                return pickle.loads(data)
            else:
                return json.loads(data.decode('utf-8'))
        except Exception as e:
            logger.error("Error deserializing cache data", error=str(e))
            raise

    async def get(self, cache_type: CacheType, identifier: str,
                 additional_params: Optional[Dict] = None) -> Optional[Any]:
        """
        Recupera dati dalla cache con metrics tracking
        """
        if not self.redis_client:
            logger.warning("Redis client not available, cache miss")
            self.metrics["misses"] += 1
            return None

        cache_key = self._generate_cache_key(cache_type, identifier, additional_params)
        config = self.cache_configs[cache_type]

        start_time = time.time()

        try:
            cached_data = self.redis_client.get(cache_key)

            if cached_data is not None:
                # Cache hit
                deserialized_data = self._deserialize_data(cached_data, config)
                self.metrics["hits"] += 1

                # Update response time metric
                response_time = time.time() - start_time
                self._update_avg_response_time(response_time)

                logger.debug("Cache hit", key=cache_key, type=cache_type.value)
                return deserialized_data
            else:
                # Cache miss
                self.metrics["misses"] += 1
                logger.debug("Cache miss", key=cache_key, type=cache_type.value)
                return None

        except Exception as e:
            logger.error("Error retrieving from cache", key=cache_key, error=str(e))
            self.metrics["errors"] += 1
            return None

    async def set(self, cache_type: CacheType, identifier: str, data: Any,
                 additional_params: Optional[Dict] = None,
                 custom_ttl: Optional[int] = None) -> bool:
        """
        Salva dati nella cache con TTL automatico
        """
        if not self.redis_client:
            logger.warning("Redis client not available, skipping cache set")
            return False

        cache_key = self._generate_cache_key(cache_type, identifier, additional_params)
        config = self.cache_configs[cache_type]
        ttl = custom_ttl or config.ttl

        try:
            serialized_data = self._serialize_data(data, config)

            # Set cache with TTL
            success = self.redis_client.setex(cache_key, ttl, serialized_data)

            if success:
                self.metrics["sets"] += 1

                # Track compression ratio
                original_size = len(pickle.dumps(data))
                cached_size = len(serialized_data)
                compression_ratio = cached_size / original_size if original_size > 0 else 1.0
                self._update_compression_ratio(compression_ratio)

                logger.debug("Cache set", key=cache_key, ttl=ttl, size=cached_size)
                return True
            else:
                logger.error("Failed to set cache", key=cache_key)
                return False

        except Exception as e:
            logger.error("Error setting cache", key=cache_key, error=str(e))
            self.metrics["errors"] += 1
            return False

    async def delete(self, cache_type: CacheType, identifier: str,
                    additional_params: Optional[Dict] = None) -> bool:
        """
        Elimina entry dalla cache
        """
        if not self.redis_client:
            return False

        cache_key = self._generate_cache_key(cache_type, identifier, additional_params)

        try:
            result = self.redis_client.delete(cache_key)
            if result > 0:
                self.metrics["deletes"] += 1
                logger.debug("Cache deleted", key=cache_key)
                return True
            else:
                logger.debug("Cache key not found for deletion", key=cache_key)
                return False

        except Exception as e:
            logger.error("Error deleting from cache", key=cache_key, error=str(e))
            self.metrics["errors"] += 1
            return False

    async def clear_by_type(self, cache_type: CacheType) -> int:
        """
        Elimina tutte le entries di un tipo specifico
        """
        if not self.redis_client:
            return 0

        pattern = f"tutor_ai:{cache_type.value}:*"
        deleted_count = 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                self.metrics["deletes"] += deleted_count
                logger.info(f"Cleared {deleted_count} entries for type {cache_type.value}")

        except Exception as e:
            logger.error("Error clearing cache by type", type=cache_type.value, error=str(e))
            self.metrics["errors"] += 1

        return deleted_count

    async def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Elimina entries basandosi su pattern
        """
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                self.metrics["deletes"] += deleted_count
                logger.info(f"Invalidated {deleted_count} entries with pattern: {pattern}")
                return deleted_count
            return 0

        except Exception as e:
            logger.error("Error invalidating cache by pattern", pattern=pattern, error=str(e))
            self.metrics["errors"] += 1
            return 0

    def _update_avg_response_time(self, response_time: float):
        """Aggiorna metrica di tempo di risposta medio"""
        current_avg = self.metrics["avg_response_time"]
        # Simple moving average
        self.metrics["avg_response_time"] = (current_avg * 0.9 + response_time * 0.1)

    def _update_compression_ratio(self, ratio: float):
        """Aggiorna metrica di compression ratio"""
        current_ratio = self.metrics["compression_ratio"]
        self.metrics["compression_ratio"] = (current_ratio * 0.9 + ratio * 0.1)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Restituisce le metriche di performance della cache
        """
        total_requests = self.metrics["hits"] + self.metrics["misses"]
        hit_rate = self.metrics["hits"] / total_requests if total_requests > 0 else 0

        return {
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "hits": self.metrics["hits"],
            "misses": self.metrics["misses"],
            "sets": self.metrics["sets"],
            "deletes": self.metrics["deletes"],
            "errors": self.metrics["errors"],
            "compression_ratio": self.metrics["compression_ratio"],
            "avg_response_time_ms": self.metrics["avg_response_time"] * 1000,
            "redis_connected": self.redis_client is not None
        }

    def get_redis_info(self) -> Dict[str, Any]:
        """
        Restituisce informazioni sul server Redis
        """
        if not self.redis_client:
            return {"connected": False}

        try:
            info = self.redis_client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "used_memory_peak": info.get("used_memory_peak_human", "N/A"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error("Error getting Redis info", error=str(e))
            return {"connected": False, "error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """
        Health check per il servizio cache
        """
        redis_healthy = False
        redis_latency = None

        if self.redis_client:
            try:
                start_time = time.time()
                self.redis_client.ping()
                redis_latency = (time.time() - start_time) * 1000  # ms
                redis_healthy = True
            except Exception as e:
                logger.error("Redis health check failed", error=str(e))

        metrics = self.get_metrics()
        return {
            "healthy": redis_healthy,
            "redis_latency_ms": redis_latency,
            "cache_metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }

    def close(self):
        """
        Chiude le connessioni Redis
        """
        if self.redis_client:
            self.redis_client.close()
        if self.connection_pool:
            self.connection_pool.disconnect()

# Decorators for easy caching
def cache_result(cache_type: CacheType, ttl: Optional[int] = None,
                key_generator: Optional[callable] = None):
    """
    Decorator per cache automatica dei risultati di funzioni
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Default key generation
                func_name = func.__name__
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = hashlib.md5((func_name + args_str).encode()).hexdigest()

            # Try to get from cache
            cache_service = RedisCacheService()
            cached_result = await cache_service.get(cache_type, cache_key)

            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_type, cache_key, result, custom_ttl=ttl)

            return result

        return wrapper
    return decorator

# Global cache instance
cache_service = None

def get_cache_service() -> RedisCacheService:
    """
    Get singleton cache service instance
    """
    global cache_service
    if cache_service is None:
        cache_service = RedisCacheService()
    return cache_service