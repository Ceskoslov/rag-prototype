import json

import chromadb
import pytest
from fakeredis import FakeRedis
from httpx import ASGITransport, AsyncClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.core.docstore import RedisDocStore
from app.core.embeddings import MockEmbeddings
from app.main import app
from app.repositories.vectorstore import ChromaRepository
from app.routers import chat
from app.services.chat import ChatService
from app.services.chunking import ChunkingService
from app.services.ingestion import IngestionService
from app.services.rag import RAGService
from app.services.retrieval import HybridRetriever


@pytest.mark.asyncio
async def test_ingest_chat_stream_sources_and_session_history(
    tmp_path, async_session_factory_test
):
    data = tmp_path / "data"
    (data / "policies").mkdir(parents=True)
    (data / "policies" / "refund.md").write_text(
        "Refund requests must be submitted within 30 days."
    )
    repository = ChromaRepository(
        chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    )
    store = RedisDocStore(redis_client=FakeRedis(decode_responses=True))
    embeddings = MockEmbeddings()
    await IngestionService(repository, store, ChunkingService(), embeddings).ingest_all(
        data
    )
    rag = RAGService(
        FakeListChatModel(
            responses=[
                "Refund requests must be submitted within 30 days [1].",
                '{"status":"approved","confidence":0.95}',
            ]
        ),
        HybridRetriever(repository, store, embeddings),
    )

    async def service():
        async with async_session_factory_test() as session:
            yield ChatService(session, rag)

    async def database():
        async with async_session_factory_test() as session:
            yield session

    app.dependency_overrides[chat.get_chat_service] = service
    app.dependency_overrides[chat.get_db] = database
    headers = {"X-API-Key": "test-api-key-12345"}
    try:
        async with AsyncClient(
            transport=ASGITransport(app), base_url="http://test", headers=headers
        ) as client:
            response = await client.post(
                "/api/v1/chat/stream",
                json={
                    "message": "Refund request window?",
                    "knowledge_base": "policies",
                    "session_id": "e2e-session",
                },
            )
            assert response.status_code == 200
            events = [
                json.loads(line[6:])
                for line in response.text.splitlines()
                if line.startswith("data: ")
            ]
            assert any(event["type"] == "token" for event in events)
            assert events[-1]["type"] == "done"
            assert events[-1]["data"]["grounded"]
            sources = next(
                event["data"] for event in events if event["type"] == "sources"
            )
            assert sources[0]["citation_id"] == 1
            assert "30 days" in sources[0]["content"]
            assert sources[0]["index_version"].startswith("idx_")
            history = (await client.get("/api/v1/sessions/e2e-session/messages")).json()
            assert [message["role"] for message in history["messages"]] == [
                "user",
                "assistant",
            ]
            assert (
                history["messages"][1]["sources"][0]["content"] == sources[0]["content"]
            )
            assert (await client.get("/api/v1/sessions")).json()[0][
                "session_id"
            ] == "e2e-session"
    finally:
        app.dependency_overrides.clear()
