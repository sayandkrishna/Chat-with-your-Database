import redis
import hashlib
import time
import numpy as np
from typing import Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from models import SemanticCacheEntry
from config import settings
from functools import lru_cache


class CacheManager:
    """Manages Redis caching operations and semantic caching."""

    def __init__(self):
        self.client = None
        self.embedding_model = None
        self._setup_redis()
        self._setup_embedding_model()

    def _setup_redis(self):
        """Setup Redis connection."""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            self.client.ping()
            print("✅ Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            print(f"⚠️ Could not connect to Redis: {e}. Caching will be disabled.")
            self.client = None

    def _setup_embedding_model(self):
        """Setup the sentence transformer model for embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            print("🔄 Loading sentence transformer model...")
            # Load on GPU if available, normalize embeddings
            self.embedding_model = SentenceTransformer(
                'sentence-transformers/all-MiniLM-L6-v2',
                device="cuda" if self._has_cuda() else "cpu"
            )
            print("✅ Embedding model loaded successfully.")
        except Exception as e:
            print(f"⚠️ Failed to load embedding model: {e}")
            self.embedding_model = None

    def _has_cuda(self):
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    @lru_cache(maxsize=1000)
    def get_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """Generate normalized embedding for a query."""
        if not self.embedding_model:
            return None
        try:
            embedding = self.embedding_model.encode(
                [query.lower().strip()],
                normalize_embeddings=True
            )[0]
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def store_semantic_cache(self, user_id: str, query: str, embedding: np.ndarray, response: Dict[str, Any]):
        """Store query-response pair with embedding in Redis."""
        if not self.client:
            return

        try:
            cache_entry = SemanticCacheEntry(
                query=query,
                embedding=embedding.tolist(),
                response=response,
                timestamp=time.time(),
                user_id=user_id
            )

            # Unique cache key
            cache_key = f"semantic_cache:{user_id}:{hashlib.sha256(query.encode()).hexdigest()[:16]}"

            pipe = self.client.pipeline()
            pipe.setex(cache_key, settings.CACHE_EXPIRATION_SECONDS, cache_entry.json())
            pipe.sadd(f"semantic_index:{user_id}", cache_key)
            pipe.expire(f"semantic_index:{user_id}", settings.CACHE_EXPIRATION_SECONDS)
            pipe.execute()

            print(f"✅ Stored semantic cache entry: {cache_key}")
        except Exception as e:
            print(f"Error storing semantic cache: {e}")

    def find_similar_cached_query(self, user_id: str, query: str, query_embedding: np.ndarray) -> Optional[Dict[str, Any]]:
        """Find semantically similar cached queries using vector similarity."""
        if not self.client:
            return None

        try:
            index_key = f"semantic_index:{user_id}"
            cached_keys = list(self.client.smembers(index_key))
            if not cached_keys:
                return None

            # Fetch all entries in one pipeline call
            pipe = self.client.pipeline()
            for key in cached_keys:
                pipe.get(key)
            cached_data_list = pipe.execute()

            embeddings = []
            entries = []
            for cached_data in cached_data_list:
                if not cached_data:
                    continue
                try:
                    entry = SemanticCacheEntry.parse_raw(cached_data)
                    embeddings.append(entry.embedding)
                    entries.append(entry)
                except Exception:
                    continue

            if not embeddings:
                return None

            # Vectorized similarity computation
            embeddings_np = np.array(embeddings, dtype=np.float32)
            similarities = cosine_similarity(query_embedding.reshape(1, -1), embeddings_np)[0]

            best_idx = np.argmax(similarities)
            best_similarity = similarities[best_idx]

            if best_similarity > settings.SEMANTIC_SIMILARITY_THRESHOLD:
                best_entry = entries[best_idx]
                print(f"🎯 Found similar query (similarity: {best_similarity:.3f})")
                print(f"   Original: {best_entry.query}")
                print(f"   Current:  {query}")

                # Update hit count
                try:
                    best_entry.hit_count += 1
                    self.client.setex(
                        cached_keys[best_idx],
                        settings.CACHE_EXPIRATION_SECONDS,
                        best_entry.json()
                    )
                except:
                    pass

                return {
                    "response": best_entry.response,
                    "similarity": float(best_similarity),
                    "original_query": best_entry.query
                }

            return None
        except Exception as e:
            print(f"Error finding similar cached query: {e}")
            return None

    def get_cache_stats(self, user_id: str) -> Dict[str, Any]:
        """Get semantic cache statistics for a specific user."""
        if not self.client:
            return {"error": "Cache not available"}

        try:
            index_key = f"semantic_index:{user_id}"
            cached_keys = list(self.client.smembers(index_key))

            pipe = self.client.pipeline()
            for key in cached_keys:
                pipe.get(key)
            cached_data_list = pipe.execute()

            stats = {
                "total_cached_queries": len(cached_keys),
                "cache_entries": []
            }

            for cached_data in cached_data_list:
                if cached_data:
                    try:
                        cache_entry = SemanticCacheEntry.parse_raw(cached_data)
                        stats["cache_entries"].append({
                            "query": cache_entry.query,
                            "hit_count": cache_entry.hit_count,
                            "timestamp": cache_entry.timestamp,
                            "response_type": cache_entry.response.get("action", "query")
                        })
                    except:
                        continue

            stats["cache_entries"].sort(key=lambda x: x["hit_count"], reverse=True)
            return stats
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {"error": "Failed to retrieve cache statistics"}

    def clear_user_cache(self, user_id: str) -> Dict[str, Any]:
        """Clear all cached queries for a specific user."""
        if not self.client:
            return {"error": "Cache not available"}

        try:
            index_key = f"semantic_index:{user_id}"
            cached_keys = list(self.client.smembers(index_key))

            pipe = self.client.pipeline()
            for key in cached_keys:
                pipe.delete(key)
            pipe.delete(index_key)
            pipe.execute()

            return {
                "message": f"Cleared {len(cached_keys)} cached queries",
                "cleared_count": len(cached_keys)
            }
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return {"error": "Failed to clear cache"}


# Global cache manager instance
cache_manager = CacheManager()
