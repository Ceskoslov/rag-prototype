from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import pytest
from sqlalchemy import select

from app.agents.supervisor import SupervisorResult
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.common import Department
from app.services.chat import ChatService


@dataclass
class FakeSupervisor:
    result: SupervisorResult
    calls: list[dict[str, Any]] = field(default_factory=list)

    def route_query(
        self,
        query: str,
        department: Department | None = None,
        config: dict[str, Any] | None = None,
    ) -> SupervisorResult:
        self.calls.append({"query": query, "department": department, "config": config})
        return self.result


def _supervisor_result(
    answer: str = "Reset your VPN password in the portal.",
    departments: list[Department] | None = None,
    traces: list[dict[str, Any]] | None = None,
    confidence: float = 0.91,
) -> SupervisorResult:
    return SupervisorResult(
        answer=answer,
        departments_used=departments or [Department.IT_SUPPORT],
        agent_traces=traces
        or [
            {
                "routing_decision": {
                    "departments": [Department.IT_SUPPORT.value],
                    "confidence": confidence,
                },
                "sources": [
                    {
                        "title": "VPN Guide",
                        "snippet": "Reset from SSO profile page",
                        "department": Department.IT_SUPPORT.value,
                    }
                ],
            }
        ],
        confidence=confidence,
    )


@pytest.mark.asyncio
async def test_chat_service_creates_new_conversation(
    async_session_factory_test,
) -> None:
    async with async_session_factory_test() as session:
        supervisor = FakeSupervisor(_supervisor_result())
        service = ChatService(session=session, supervisor=supervisor)

        response = await service.process_message(
            message="How do I reset VPN?",
            department=Department.IT_SUPPORT,
            session_id=None,
        )

        assert response.answer
        assert response.department == Department.IT_SUPPORT

        conversations = (
            (
                await session.execute(
                    select(Conversation).where(Conversation.session_id.is_not(None))
                )
            )
            .scalars()
            .all()
        )
        assert len(conversations) == 1

        saved_messages = (
            (
                await session.execute(
                    select(Message).where(
                        Message.conversation_id == conversations[0].id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(saved_messages) == 2
        assert saved_messages[0].role == "user"
        assert saved_messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_chat_service_loads_history(async_session_factory_test) -> None:
    async with async_session_factory_test() as session:
        supervisor = FakeSupervisor(_supervisor_result())
        service = ChatService(session=session, supervisor=supervisor)

        preseed_id = "session-history-15"
        await service.process_message(
            message="seed",
            department=Department.IT_SUPPORT,
            session_id=preseed_id,
        )

        conversation = (
            await session.execute(
                select(Conversation).where(Conversation.session_id == preseed_id)
            )
        ).scalar_one()

        for i in range(13):
            session.add(
                Message(
                    conversation_id=conversation.id,
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"history-{i}",
                )
            )
        await session.commit()

        captured: dict[str, Any] = {}
        original = service.conversation_repo.get_messages

        async def wrapped(conversation_id: int, limit: int = 10, offset: int = 0):
            result = await original(conversation_id, limit=limit, offset=offset)
            captured["conversation_id"] = conversation_id
            captured["limit"] = limit
            captured["history"] = [
                {"role": item.role, "content": item.content} for item in result
            ]
            return result

        service.conversation_repo.get_messages = wrapped  # type: ignore[method-assign]

        await service.process_message(
            message="new-question",
            department=Department.IT_SUPPORT,
            session_id=preseed_id,
        )

        assert captured["conversation_id"] == conversation.id
        assert captured["limit"] == 10
        assert len(captured["history"]) == 10
        assert captured["history"][0]["content"].startswith("history")


@pytest.mark.asyncio
async def test_chat_service_routes_through_supervisor(
    async_session_factory_test,
) -> None:
    async with async_session_factory_test() as session:
        supervisor = FakeSupervisor(
            _supervisor_result(departments=[Department.CREDIT_CARD], confidence=0.84)
        )
        service = ChatService(session=session, supervisor=supervisor)

        await service.process_message(
            message="How many miles expire this year?",
            department=Department.CREDIT_CARD,
            session_id="route-session",
        )

        assert len(supervisor.calls) == 1
        assert supervisor.calls[0]["query"] == "How many miles expire this year?"
        assert supervisor.calls[0]["department"] == Department.CREDIT_CARD


@pytest.mark.asyncio
async def test_chat_service_saves_response_with_trace(
    async_session_factory_test,
) -> None:
    async with async_session_factory_test() as session:
        trace_payload = [
            {
                "routing_decision": {
                    "departments": [Department.LEGAL.value],
                    "confidence": 0.77,
                },
                "sources": [
                    {
                        "title": "EU261",
                        "snippet": "Compensation policy",
                        "department": Department.LEGAL.value,
                    }
                ],
            }
        ]
        supervisor = FakeSupervisor(
            _supervisor_result(
                answer="Legal reviewed your request.",
                departments=[Department.LEGAL],
                traces=trace_payload,
                confidence=0.77,
            )
        )
        service = ChatService(session=session, supervisor=supervisor)

        response = await service.process_message(
            message="Can I claim compensation?",
            department=Department.LEGAL,
            session_id="legal-session",
        )

        assert response.confidence == 0.77
        assert response.trace.supervisor_decision
        assert Department.LEGAL.value in response.trace.supervisor_decision

        conversation = (
            await session.execute(
                select(Conversation).where(Conversation.session_id == "legal-session")
            )
        ).scalar_one()
        assistant_message = (
            await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .where(Message.role == "assistant")
            )
        ).scalar_one()

        assert assistant_message.sources is not None
        assert assistant_message.trace is not None
        assert assistant_message.trace["agent_traces"] == trace_payload
        assert assistant_message.trace["confidence"] == 0.77


@pytest.mark.asyncio
async def test_chat_stream_yields_correct_event_types(
    async_session_factory_test,
) -> None:
    async with async_session_factory_test() as session:
        supervisor = FakeSupervisor(
            _supervisor_result(
                answer="Token one token two",
                departments=[Department.IT_SUPPORT],
                confidence=0.8,
            )
        )
        service = ChatService(session=session, supervisor=supervisor)

        events: list[dict[str, Any]] = []
        async for chunk in service.chat_stream(
            message="stream this",
            department=Department.IT_SUPPORT,
            session_id="stream-session",
        ):
            assert chunk.startswith("data: ")
            assert chunk.endswith("\n\n")
            payload = json.loads(chunk[len("data: ") :].strip())
            events.append(payload)

        types = [event["type"] for event in events]
        assert "token" in types
        assert "sources" in types
        assert "trace" in types
        assert "done" in types
        assert "heartbeat" in types


@pytest.mark.asyncio
async def test_chat_service_passes_config_with_thread_id(
    async_session_factory_test,
) -> None:
    """Verify that chat service passes config with thread_id to supervisor."""
    async with async_session_factory_test() as session:
        supervisor = FakeSupervisor(_supervisor_result())
        service = ChatService(session=session, supervisor=supervisor)

        session_id = "config-thread-session"
        await service.process_message(
            message="Test message",
            department=Department.IT_SUPPORT,
            session_id=session_id,
        )

        # Verify supervisor was called with config containing thread_id
        assert len(supervisor.calls) == 1
        call = supervisor.calls[0]
        assert call["config"] is not None
        assert "configurable" in call["config"]
        assert "thread_id" in call["config"]["configurable"]
        # thread_id should be conversation.id (an integer)
        assert isinstance(call["config"]["configurable"]["thread_id"], int)
