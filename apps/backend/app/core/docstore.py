"""Redis-backed document store for parent document persistence."""

import json
from collections.abc import Iterator, Sequence

import redis
from langchain_core.documents import Document
from langchain_core.stores import BaseStore


class RedisDocStore(BaseStore[str, Document]):
    """Redis-backed store for LangChain Document objects.

    Implements BaseStore interface for storing and retrieving Document objects
    in Redis with JSON serialization. Uses a key prefix for namespacing.

    Key format: {prefix}:{key}
    Example: docstore:product_docs:doc123
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "docstore",
        redis_client: redis.Redis | None = None,
    ):
        """Initialize Redis document store.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            prefix: Key prefix for namespacing (default: "docstore")
            redis_client: Optional pre-configured Redis client (for testing with fakeredis)
        """
        if redis_client is not None:
            self.client = redis_client
        else:
            self.client = redis.from_url(redis_url, decode_responses=True)
        self.prefix = prefix

    def _make_key(self, key: str) -> str:
        """Create full Redis key with prefix."""
        return f"{self.prefix}:{key}"

    def _serialize_document(self, doc: Document) -> str:
        """Serialize Document to JSON string."""
        return json.dumps(
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
            }
        )

    def _deserialize_document(self, data: str) -> Document:
        """Deserialize JSON string to Document."""
        obj = json.loads(data)
        return Document(
            page_content=obj["page_content"],
            metadata=obj["metadata"],
        )

    def mget(self, keys: Sequence[str]) -> list[Document | None]:
        """Get the values associated with the given keys.

        Args:
            keys: A sequence of keys.

        Returns:
            A list of optional Document objects. If a key is not found,
            the corresponding value will be None.
        """
        if not keys:
            return []

        redis_keys = [self._make_key(key) for key in keys]
        values = self.client.mget(redis_keys)

        results = []
        for value in values:
            if value is None:
                results.append(None)
            else:
                results.append(self._deserialize_document(value))

        return results

    def mset(self, key_value_pairs: Sequence[tuple[str, Document]]) -> None:
        """Set the values for the given keys.

        Args:
            key_value_pairs: A sequence of (key, Document) tuples.
        """
        if not key_value_pairs:
            return

        mapping = {
            self._make_key(key): self._serialize_document(doc)
            for key, doc in key_value_pairs
        }
        self.client.mset(mapping)

    def mdelete(self, keys: Sequence[str]) -> None:
        """Delete the given keys and their associated values.

        Args:
            keys: A sequence of keys to delete.
        """
        if not keys:
            return

        redis_keys = [self._make_key(key) for key in keys]
        self.client.delete(*redis_keys)

    def yield_keys(self, *, prefix: str | None = None) -> Iterator[str]:
        """Get an iterator over keys that match the given prefix.

        Args:
            prefix: Optional prefix to filter keys. If None, returns all keys
                   with the store's prefix.

        Yields:
            Iterator over keys (without the store's prefix).
        """
        if prefix is None:
            pattern = f"{self.prefix}:*"
        else:
            pattern = f"{self.prefix}:{prefix}*"

        for redis_key in self.client.scan_iter(match=pattern):
            key_without_prefix = redis_key[len(self.prefix) + 1 :]
            yield key_without_prefix
