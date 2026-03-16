"""Tests for RedisDocStore implementation."""

import pytest
from fakeredis import FakeRedis
from langchain_core.documents import Document

from app.core.docstore import RedisDocStore


@pytest.fixture
def redis_store():
    """Create a RedisDocStore instance using fakeredis."""
    fake_redis = FakeRedis(decode_responses=True)
    store = RedisDocStore(redis_client=fake_redis, prefix="docstore:it_support")
    yield store
    fake_redis.flushdb()


def test_mset_and_mget(redis_store):
    """Test storing and retrieving documents."""
    # Create test documents
    doc1 = Document(page_content="Test content 1", metadata={"source": "file1.txt"})
    doc2 = Document(page_content="Test content 2", metadata={"source": "file2.txt"})

    # Store documents
    redis_store.mset([("doc1", doc1), ("doc2", doc2)])

    # Retrieve documents
    results = redis_store.mget(["doc1", "doc2", "doc3"])

    # Verify results
    assert len(results) == 3
    assert results[0] is not None
    assert results[0].page_content == "Test content 1"
    assert results[0].metadata == {"source": "file1.txt"}
    assert results[1] is not None
    assert results[1].page_content == "Test content 2"
    assert results[1].metadata == {"source": "file2.txt"}
    assert results[2] is None  # doc3 doesn't exist


def test_mdelete(redis_store):
    """Test deleting documents."""
    # Create and store documents
    doc1 = Document(page_content="Test content 1", metadata={"source": "file1.txt"})
    doc2 = Document(page_content="Test content 2", metadata={"source": "file2.txt"})
    redis_store.mset([("doc1", doc1), ("doc2", doc2)])

    # Verify documents exist
    results = redis_store.mget(["doc1", "doc2"])
    assert results[0] is not None
    assert results[1] is not None

    # Delete doc1
    redis_store.mdelete(["doc1"])

    results = redis_store.mget(["doc1", "doc2"])
    assert results[0] is None
    assert results[1] is not None


def test_yield_keys(redis_store):
    """Test iterating over keys with prefix filtering."""
    # Store documents
    doc1 = Document(page_content="Content 1", metadata={})
    doc2 = Document(page_content="Content 2", metadata={})
    doc3 = Document(page_content="Content 3", metadata={})
    redis_store.mset([("user:123", doc1), ("user:456", doc2), ("system:789", doc3)])

    # Get all keys
    all_keys = list(redis_store.yield_keys())
    assert len(all_keys) == 3
    assert "user:123" in all_keys
    assert "user:456" in all_keys
    assert "system:789" in all_keys

    # Get keys with prefix
    user_keys = list(redis_store.yield_keys(prefix="user:"))
    assert len(user_keys) == 2
    assert "user:123" in user_keys
    assert "user:456" in user_keys


def test_persistence_across_instances():
    """Test that documents persist when store is recreated."""
    fake_redis = FakeRedis(decode_responses=True)

    store1 = RedisDocStore(redis_client=fake_redis, prefix="docstore:test")
    doc = Document(page_content="Persistent content", metadata={"id": "persist1"})
    store1.mset([("persist_doc", doc)])

    store2 = RedisDocStore(redis_client=fake_redis, prefix="docstore:test")

    results = store2.mget(["persist_doc"])
    assert results[0] is not None
    assert results[0].page_content == "Persistent content"
    assert results[0].metadata == {"id": "persist1"}

    fake_redis.flushdb()


def test_document_with_complex_metadata(redis_store):
    """Test storing documents with complex metadata."""
    # Create document with complex metadata
    doc = Document(
        page_content="Complex document",
        metadata={
            "source": "file.txt",
            "department": "it_support",
            "tags": ["important", "urgent"],
            "score": 0.95,
            "nested": {"key": "value"},
        },
    )

    # Store and retrieve
    redis_store.mset([("complex_doc", doc)])
    results = redis_store.mget(["complex_doc"])

    # Verify metadata is preserved
    assert results[0] is not None
    assert results[0].page_content == "Complex document"
    assert results[0].metadata["department"] == "it_support"
    assert results[0].metadata["tags"] == ["important", "urgent"]
    assert results[0].metadata["score"] == 0.95
    assert results[0].metadata["nested"] == {"key": "value"}
