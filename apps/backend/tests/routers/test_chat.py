from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncGenerator

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.agents.supervisor import SupervisorResult
from app.middleware.auth import verify_api_key
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import AgentTrace, ChatResponse
from app.schemas.common import Department


@dataclass
class FakeChatService:
    response: ChatResponse
    stream_events: list[dict[str, Any]]

    async def process_message(
        self,
        message: str,
        department: Department | None = None,
        session_id: str | None = None,
    ) -> ChatResponse:
        _ = (message, department, session_id)
        return self.response

    async def chat_stream(
        self,
        message: str,
        department: Department | None = None,
        session_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        _ = (message, department, session_id)
        for event in self.stream_events:
            yield f"data: {json.dumps(event)}\n\n"


@pytest.fixture
def app_with_chat():
    from app.routers import chat as chat_router

    app = FastAPI(dependencies=[Depends(verify_api_key)])
    app.include_router(chat_router.router)
    return app


@pytest.fixture
def default_fake_service() -> FakeChatService:
    return FakeChatService(
        response=ChatResponse(
            answer="Reset your VPN using SSO self-service.",
            department=Department.IT_SUPPORT,
            sources=["vpn-runbook.md"],
            confidence=0.91,
            trace=AgentTrace(
                supervisor_decision="it_support",
                agents_invoked=["it_support_agent"],
                retrieval_sources=[{"title": "VPN", "snippet": "SSO reset"}],
                iterations=1,
            ),
            session_id="session-router-1",
        ),
        stream_events=[
            {"type": "token", "content": "Reset"},
            {"type": "token", "content": "your"},
            {"type": "sources", "data": [{"title": "VPN", "snippet": "SSO"}]},
            {
                "type": "trace",
                "data": {"departments": ["it_support"], "confidence": 0.91},
            },
            {"type": "done"},
        ],
    )


@pytest.mark.asyncio
async def test_chat_endpoint_returns_structured_response(
    app_with_chat: FastAPI,
    default_fake_service: FakeChatService,
) -> None:
    from app.routers import chat as chat_router

    async def override_chat_service() -> FakeChatService:
        return default_fake_service

    app_with_chat.dependency_overrides[chat_router.get_chat_service] = (
        override_chat_service
    )

    transport = ASGITransport(app=app_with_chat)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "My VPN fails", "department": "it_support"},
            headers={"X-API-Key": "test-api-key-12345"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"]
    assert data["department"] == Department.IT_SUPPORT.value
    assert isinstance(data["sources"], list)
    assert isinstance(data["confidence"], float)
    assert "trace" in data
    assert "session_id" in data


@pytest.mark.asyncio
async def test_chat_endpoint_requires_api_key(
    app_with_chat: FastAPI,
    default_fake_service: FakeChatService,
) -> None:
    from app.routers import chat as chat_router

    async def override_chat_service() -> FakeChatService:
        return default_fake_service

    app_with_chat.dependency_overrides[chat_router.get_chat_service] = (
        override_chat_service
    )

    transport = ASGITransport(app=app_with_chat)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "My VPN fails", "department": "it_support"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_stream_delivers_sse_events(
    app_with_chat: FastAPI,
    default_fake_service: FakeChatService,
) -> None:
    from app.routers import chat as chat_router

    async def override_chat_service() -> FakeChatService:
        return default_fake_service

    app_with_chat.dependency_overrides[chat_router.get_chat_service] = (
        override_chat_service
    )

    transport = ASGITransport(app=app_with_chat)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/stream",
            json={"message": "Stream VPN help", "department": "it_support"},
            headers={"X-API-Key": "test-api-key-12345"},
        )

    assert response.status_code == 200
    lines = [line for line in response.text.splitlines() if line.startswith("data: ")]
    assert len(lines) >= 4

    payloads = [json.loads(line[len("data: ") :]) for line in lines]
    event_types = {payload["type"] for payload in payloads}
    assert "token" in event_types
    assert "sources" in event_types
    assert "trace" in event_types
    assert "done" in event_types


@pytest.mark.asyncio
async def test_chat_stream_includes_done_event(
    app_with_chat: FastAPI,
    default_fake_service: FakeChatService,
) -> None:
    from app.routers import chat as chat_router

    async def override_chat_service() -> FakeChatService:
        return default_fake_service

    app_with_chat.dependency_overrides[chat_router.get_chat_service] = (
        override_chat_service
    )

    transport = ASGITransport(app=app_with_chat)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/stream",
            json={"message": "Stream VPN help", "department": "it_support"},
            headers={"X-API-Key": "test-api-key-12345"},
        )

    lines = [line for line in response.text.splitlines() if line.startswith("data: ")]
    payloads = [json.loads(line[len("data: ") :]) for line in lines]
    assert payloads[-1]["type"] == "done"


@pytest.mark.asyncio
async def test_invalid_request_body_returns_422(
    app_with_chat: FastAPI,
    default_fake_service: FakeChatService,
) -> None:
    from app.routers import chat as chat_router

    async def override_chat_service() -> FakeChatService:
        return default_fake_service

    app_with_chat.dependency_overrides[chat_router.get_chat_service] = (
        override_chat_service
    )

    transport = ASGITransport(app=app_with_chat)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"department": "it_support"},
            headers={"X-API-Key": "test-api-key-12345"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_conversation_saved_to_database(
    app_with_chat: FastAPI,
    async_session_factory_test,
) -> None:
    from app.routers import chat as chat_router
    from app.services.chat import ChatService

    class FakeSupervisor:
        def route_query(
            self, query: str, department: Department | None = None
        ) -> SupervisorResult:
            _ = (query, department)
            return SupervisorResult(
                answer="Saved response",
                departments_used=[Department.IT_SUPPORT],
                agent_traces=[
                    {
                        "routing_decision": {
                            "departments": [Department.IT_SUPPORT.value],
                            "confidence": 0.85,
                        },
                        "sources": [
                            {
                                "title": "VPN",
                                "snippet": "Saved",
                                "department": Department.IT_SUPPORT.value,
                            }
                        ],
                    }
                ],
                confidence=0.85,
            )

    async def override_get_db():
        async with async_session_factory_test() as session:
            yield session
            await session.commit()

    async def override_chat_service(db=Depends(override_get_db)):
        return ChatService(session=db, supervisor=FakeSupervisor())

    app_with_chat.dependency_overrides[chat_router.get_db] = override_get_db
    app_with_chat.dependency_overrides[chat_router.get_chat_service] = (
        override_chat_service
    )

    transport = ASGITransport(app=app_with_chat)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "Persist this conversation",
                "department": "it_support",
                "session_id": "persist-session-1",
            },
            headers={"X-API-Key": "test-api-key-12345"},
        )

    assert response.status_code == 200

    async with async_session_factory_test() as verify_session:
        conversation = (
            await verify_session.execute(
                select(Conversation).where(
                    Conversation.session_id == "persist-session-1"
                )
            )
        ).scalar_one()
        messages = (
            (
                await verify_session.execute(
                    select(Message).where(Message.conversation_id == conversation.id)
                )
            )
            .scalars()
            .all()
        )

        assert len(messages) == 2
        assert any(msg.role == "user" for msg in messages)
        assert any(msg.role == "assistant" for msg in messages)
