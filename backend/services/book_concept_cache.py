#!/usr/bin/env python3
"""
Servizio di cache ottimizzato per book concept maps RAG-based
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog

logger = structlog.get_logger()


class BookConceptCache:
    """
    Cache layer per book concept maps con:
    - Cache basata su qualità RAG
    - TTL configurabile
    - Background refresh
    - Metrics tracking
    """

    def __init__(self, cache_path: str = "data/book_concept_cache.json"):
        self.cache_path = Path(cache_path)
        self.cache_data = {}
        self.metrics_path = Path("data/cache_metrics.json")
        self.metrics = {}
        self._ensure_cache_structure()
        self._load_cache()

    def _ensure_cache_structure(self):
        """Assicura che le directory e i file di cache esistano"""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.cache_path.exists():
            self.cache_path.write_text(json.dumps({
                "book_concepts": {},
                "last_cleanup": datetime.now().isoformat(),
                "cache_stats": {
                    "total_entries": 0,
                    "hit_rate": 0.0,
                    "avg_quality": 0.0
                }
            }, indent=2), encoding='utf-8')

        if not self.metrics_path.exists():
            self.metrics_path.write_text(json.dumps({
                "cache_hits": 0,
                "cache_misses": 0,
                "rag_saves": 0,
                "fallback_saves": 0,
                "background_refreshes": 0,
                "avg_response_time": 0.0,
                "last_updated": datetime.now().isoformat()
            }, indent=2), encoding='utf-8')

    def _load_cache(self):
        """Carica i dati di cache"""
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                self.cache_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self.cache_data = {"book_concepts": {}, "cache_stats": {}}

        try:
            with open(self.metrics_path, 'r', encoding='utf-8') as f:
                self.metrics = json.load(f)
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
            self.metrics = {}

    def _save_cache(self):
        """Salva i dati di cache"""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _save_metrics(self):
        """Salva le metrics"""
        try:
            with open(self.metrics_path, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    def _get_cache_key(self, course_id: str, book_id: str, quality_threshold: float = 0.6) -> str:
        """Genera chiave di cache univoca"""
        key_data = f"{course_id}_{book_id}_{quality_threshold}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get_concept_map(self, course_id: str, book_id: str, quality_threshold: float = 0.6) -> Optional[Dict[str, Any]]:
        """
        Recupera concept map dalla cache se valida
        """
        try:
            start_time = time.time()
            cache_key = self._get_cache_key(course_id, book_id, quality_threshold)

            # Check if exists in cache
            if cache_key not in self.cache_data.get("book_concepts", {}):
                self._record_miss()
                return None

            cached_entry = self.cache_data["book_concepts"][cache_key]

            # Check TTL
            if self._is_expired(cached_entry):
                self._record_miss()
                self._schedule_background_refresh(course_id, book_id, quality_threshold)
                return None

            # Check quality threshold
            cached_quality = cached_entry.get("rag_analysis_quality_score", 0.0)
            if cached_quality < quality_threshold:
                self._record_miss()
                logger.info(f"Cache entry below quality threshold: {cached_quality} < {quality_threshold}")
                return None

            # Valid cache entry found
            response_time = time.time() - start_time
            self._record_hit(response_time)

            logger.info(f"Cache hit for book {book_id}, quality: {cached_quality:.2f}, response_time: {response_time:.3f}s")

            # Return cached concept map
            return cached_entry.get("concept_map", {})

        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            self._record_miss()
            return None

    def store_concept_map(self, course_id: str, book_id: str, concept_map: Dict[str, Any],
                         quality_threshold: float = 0.6, ttl_hours: int = 24) -> bool:
        """
        Salva concept map nella cache
        """
        try:
            cache_key = self._get_cache_key(course_id, book_id, quality_threshold)
            quality_score = concept_map.get("rag_analysis_quality_score", 0.0)

            # Only cache if meets minimum quality
            if quality_score < quality_threshold * 0.8:  # Allow slightly lower for caching
                logger.warning(f"Concept map quality too low for caching: {quality_score}")
                return False

            cache_entry = {
                "course_id": course_id,
                "book_id": book_id,
                "quality_threshold": quality_threshold,
                "concept_map": concept_map,
                "rag_analysis_quality_score": quality_score,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=ttl_hours)).isoformat(),
                "access_count": 0,
                "last_accessed": datetime.now().isoformat()
            }

            # Store in cache
            if "book_concepts" not in self.cache_data:
                self.cache_data["book_concepts"] = {}

            self.cache_data["book_concepts"][cache_key] = cache_entry

            # Update stats
            self._update_cache_stats()
            self._save_cache()

            # Record metrics
            if concept_map.get("rag_enhanced", False):
                self._record_rag_save()
            else:
                self._record_fallback_save()

            logger.info(f"Cached concept map for book {book_id}, quality: {quality_score:.2f}, TTL: {ttl_hours}h")
            return True

        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
            return False

    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        try:
            expires_at = datetime.fromisoformat(cache_entry.get("expires_at", ""))
            return datetime.now() > expires_at
        except Exception:
            return True  # Treat invalid dates as expired

    def _record_hit(self, response_time: float):
        """Record cache hit"""
        self.metrics["cache_hits"] = self.metrics.get("cache_hits", 0) + 1
        self._update_response_time(response_time)
        self._save_metrics()

    def _record_miss(self):
        """Record cache miss"""
        self.metrics["cache_misses"] = self.metrics.get("cache_misses", 0) + 1
        self._save_metrics()

    def _record_rag_save(self):
        """Record RAG-enhanced concept map save"""
        self.metrics["rag_saves"] = self.metrics.get("rag_saves", 0) + 1
        self._save_metrics()

    def _record_fallback_save(self):
        """Record fallback concept map save"""
        self.metrics["fallback_saves"] = self.metrics.get("fallback_saves", 0) + 1
        self._save_metrics()

    def _update_response_time(self, response_time: float):
        """Update average response time"""
        current_avg = self.metrics.get("avg_response_time", 0.0)
        hits = self.metrics.get("cache_hits", 1)
        self.metrics["avg_response_time"] = (current_avg * (hits - 1) + response_time) / hits
        self._save_metrics()

    def _schedule_background_refresh(self, course_id: str, book_id: str, quality_threshold: float):
        """Schedule background refresh for expired entry"""
        # Mark for background refresh
        refresh_key = f"refresh_{course_id}_{book_id}"
        self.cache_data[refresh_key] = {
            "scheduled_at": datetime.now().isoformat(),
            "quality_threshold": quality_threshold
        }
        self._save_cache()

    def _update_cache_stats(self):
        """Update cache statistics"""
        total_entries = len(self.cache_data.get("book_concepts", {}))
        self.cache_data["cache_stats"] = {
            "total_entries": total_entries,
            "last_updated": datetime.now().isoformat()
        }
        self.cache_data["last_cleanup"] = datetime.now().isoformat()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            hit_rate = 0.0
            hits = self.metrics.get("cache_hits", 0)
            misses = self.metrics.get("cache_misses", 0)
            total_requests = hits + misses

            if total_requests > 0:
                hit_rate = hits / total_requests

            # Calculate average quality in cache
            avg_quality = 0.0
            entries = self.cache_data.get("book_concepts", {})
            if entries:
                qualities = [entry.get("rag_analysis_quality_score", 0.0) for entry in entries.values()]
                avg_quality = sum(qualities) / len(qualities)

            return {
                "cache_performance": {
                    "hit_rate": hit_rate,
                    "total_requests": total_requests,
                    "cache_hits": hits,
                    "cache_misses": misses,
                    "avg_response_time": self.metrics.get("avg_response_time", 0.0)
                },
                "cache_content": {
                    "total_entries": len(entries),
                    "avg_quality_score": avg_quality,
                    "rag_enhanced_entries": self.metrics.get("rag_saves", 0),
                    "fallback_entries": self.metrics.get("fallback_saves", 0),
                    "background_refreshes": self.metrics.get("background_refreshes", 0)
                },
                "cache_health": {
                    "last_cleanup": self.cache_data.get("last_cleanup"),
                    "cache_file_size": self.cache_path.stat().st_size if self.cache_path.exists() else 0,
                    "metrics_file_size": self.metrics_path.stat().st_size if self.metrics_path.exists() else 0
                }
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    def cleanup_expired_entries(self) -> Dict[str, int]:
        """Clean up expired cache entries"""
        try:
            removed_count = 0
            current_entries = self.cache_data.get("book_concepts", {})
            cleaned_entries = {}

            for cache_key, entry in current_entries.items():
                if not self._is_expired(entry):
                    cleaned_entries[cache_key] = entry
                else:
                    removed_count += 1
                    logger.info(f"Removed expired cache entry: {cache_key}")

            self.cache_data["book_concepts"] = cleaned_entries
            self.cache_data["last_cleanup"] = datetime.now().isoformat()
            self._save_cache()

            return {
                "entries_removed": removed_count,
                "entries_remaining": len(cleaned_entries)
            }

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"entries_removed": 0, "error": str(e)}

    def invalidate_book_cache(self, course_id: str, book_id: str) -> bool:
        """Invalidate all cache entries for a specific book"""
        try:
            removed_count = 0
            current_entries = self.cache_data.get("book_concepts", {})
            cleaned_entries = {}

            for cache_key, entry in current_entries.items():
                if (entry.get("course_id") != course_id or
                    entry.get("book_id") != book_id):
                    cleaned_entries[cache_key] = entry
                else:
                    removed_count += 1
                    logger.info(f"Invalidated cache entry for book {book_id}: {cache_key}")

            self.cache_data["book_concepts"] = cleaned_entries
            self._save_cache()

            return removed_count > 0

        except Exception as e:
            logger.error(f"Error invalidating book cache: {e}")
            return False

    def get_background_refresh_queue(self) -> List[Dict[str, Any]]:
        """Get queue of entries scheduled for background refresh"""
        refresh_queue = []

        for key, value in self.cache_data.items():
            if key.startswith("refresh_"):
                try:
                    scheduled_at = datetime.fromisoformat(value.get("scheduled_at", ""))
                    # Only return if scheduled more than 5 minutes ago (avoid immediate refresh loops)
                    if datetime.now() - scheduled_at > timedelta(minutes=5):
                        refresh_queue.append({
                            "course_id": value.get("course_id"),
                            "book_id": value.get("book_id"),
                            "quality_threshold": value.get("quality_threshold", 0.6),
                            "scheduled_at": value.get("scheduled_at")
                        })
                except Exception:
                    continue

        return refresh_queue

    def mark_refresh_completed(self, course_id: str, book_id: str):
        """Mark background refresh as completed"""
        refresh_key = f"refresh_{course_id}_{book_id}"
        if refresh_key in self.cache_data:
            del self.cache_data[refresh_key]
            self.metrics["background_refreshes"] = self.metrics.get("background_refreshes", 0) + 1
            self._save_cache()
            self._save_metrics()

    def optimize_cache_size(self, max_entries: int = 100) -> Dict[str, int]:
        """
        Optimize cache size by removing lowest quality entries
        """
        try:
            current_entries = self.cache_data.get("book_concepts", {})

            if len(current_entries) <= max_entries:
                return {"entries_removed": 0, "entries_remaining": len(current_entries)}

            # Sort by quality score (lowest first)
            sorted_entries = sorted(
                current_entries.items(),
                key=lambda x: x[1].get("rag_analysis_quality_score", 0.0)
            )

            # Keep only the best entries
            entries_to_keep = dict(sorted_entries[max_entries:])
            entries_removed = len(current_entries) - len(entries_to_keep)

            self.cache_data["book_concepts"] = entries_to_keep
            self._save_cache()

            logger.info(f"Cache optimization: removed {entries_removed} low-quality entries")
            return {
                "entries_removed": entries_removed,
                "entries_remaining": len(entries_to_keep)
            }

        except Exception as e:
            logger.error(f"Error optimizing cache size: {e}")
            return {"entries_removed": 0, "error": str(e)}


# Istanza globale del cache service
book_concept_cache = BookConceptCache()