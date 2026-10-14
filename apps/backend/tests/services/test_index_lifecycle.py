import chromadb
import pytest
from fakeredis import FakeRedis

from app.core.docstore import RedisDocStore
from app.core.embeddings import MockEmbeddings
from app.repositories.vectorstore import ChromaRepository
from app.services.chunking import ChunkingService
from app.services.ingestion import IngestionService
from app.services.retrieval import HybridRetriever, _tokenize


@pytest.fixture
def index_stack(tmp_path):
    repository = ChromaRepository(
        chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    )
    store = RedisDocStore(redis_client=FakeRedis(decode_responses=True))
    embeddings = MockEmbeddings()
    ingestion = IngestionService(repository, store, ChunkingService(), embeddings)
    retriever = HybridRetriever(repository, store, embeddings)
    data = tmp_path / "data"
    (data / "policies").mkdir(parents=True)
    return repository, store, ingestion, retriever, data


@pytest.mark.asyncio
async def test_reindex_switches_snapshots_and_refreshes_lexical_cache(index_stack):
    repo, store, ingestion, retriever, data = index_stack
    file = data / "policies" / "refund.md"
    file.write_text("退票政策：三十天内可以申请退款。", encoding="utf-8")
    await ingestion.ingest_all(data)
    first = repo.get_collection("policies").name
    assert "退票" in retriever.retrieve("退票政策", "policies")[0].page_content
    file.write_text("行李政策：最大重量二十公斤。", encoding="utf-8")
    await ingestion.ingest_all(data)
    assert repo.get_collection("policies").name != first
    assert "行李" in retriever.retrieve("行李政策", "policies")[0].page_content
    assert retriever._cache["policies"][0] == repo.get_collection("policies").name
    assert await ingestion.ingest_knowledge_base("policies", data) == 0
    file.unlink()
    await ingestion.ingest_all(data)
    assert repo.get_collection("policies").count() == 0
    assert retriever.retrieve("行李政策", "policies") == []
    old_keys = list(store.yield_keys(prefix=first + ":"))
    assert old_keys and store.client.ttl(store._make_key(old_keys[0])) > 0


@pytest.mark.asyncio
async def test_embedding_failure_preserves_active_snapshot(index_stack):
    repo, _store, ingestion, retriever, data = index_stack
    file = data / "policies" / "refund.md"
    file.write_text("Refunds within 30 days")
    await ingestion.ingest_all(data)
    active = repo.get_collection("policies").name
    file.write_text("Refunds within 60 days")

    class BrokenEmbeddings(MockEmbeddings):
        def embed_documents(self, texts):
            raise RuntimeError("provider unavailable")

    ingestion.embedding_model = BrokenEmbeddings()
    with pytest.raises(RuntimeError, match="provider unavailable"):
        await ingestion.ingest_all(data)
    assert repo.get_collection("policies").name == active
    assert "30 days" in retriever.retrieve("Refunds", "policies")[0].page_content
    assert (
        len([c for c in repo.client.list_collections() if c.name.startswith("idx_")])
        == 1
    )


def test_tokenization_handles_cjk_and_punctuation():
    assert "退款" in _tokenize("如何申请退款？")
    assert _tokenize("VPN, RESET!") == ["vpn", "reset"]


def test_pdf_pages_have_distinct_parent_ids():
    from langchain_core.documents import Document

    chunker = ChunkingService()
    documents = [
        Document(
            page_content="Repeated heading",
            metadata={
                "knowledge_base": "policies",
                "source_path": "a.pdf",
                "page": page,
            },
        )
        for page in [1, 2]
    ]
    assert (
        chunker.chunk_document(documents[0])[0].id
        != chunker.chunk_document(documents[1])[0].id
    )


@pytest.mark.asyncio
async def test_retriever_rejects_a_different_embedding_space(index_stack):
    _repo, _store, ingestion, retriever, data = index_stack
    (data / "policies" / "refund.md").write_text("Refund window is 30 days")
    await ingestion.ingest_all(data)

    class DifferentEmbeddingSpace(MockEmbeddings):
        pass

    retriever.embedding_model = DifferentEmbeddingSpace()
    with pytest.raises(ValueError, match="Embedding configuration changed"):
        retriever.retrieve("refund", "policies")
