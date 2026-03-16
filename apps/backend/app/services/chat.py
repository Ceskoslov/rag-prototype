from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.supervisor import SupervisorResult, SupervisorService
from app.core.logging import get_logger
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation import ConversationRepository
from app.schemas.chat import AgentTrace, ChatResponse
from app.schemas.common import Department

logger = get_logger(__name__)


class ChatService:
    def __init__(self, session: AsyncSession, supervisor: SupervisorService | Any):
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.supervisor = supervisor

    async def process_message(
        self,
        message: str,
        department: Department | None = None,
        session_id: str | None = None,
    ) -> ChatResponse:
        conversation = await self._get_or_create_conversation(session_id, department)
        history_messages = await self._load_recent_history(conversation.id)
        history = [
            {"role": item.role, "content": item.content} for item in history_messages
        ]
        query = self._build_query_with_history(message=message, history=history)

        try:
            result = self.supervisor.route_query(query, department)
        except Exception as exc:
            logger.error("chat_failed", error=str(exc), message=message)
            result = SupervisorResult(
                answer="I couldn't complete your request right now. Please try again.",
                departments_used=[department] if department is not None else [],
                agent_traces=[{"error": str(exc)}],
                confidence=0.0,
            )

        await self.conversation_repo.add_message(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )

        source_docs = self._extract_sources(result)
        assistant_trace = {
            "agent_traces": result.agent_traces,
            "confidence": result.confidence,
            "history_count": len(history),
        }
        await self.conversation_repo.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=result.answer,
            sources=source_docs,
            trace=assistant_trace,
        )

        await self.session.commit()
        return self._to_chat_response(
            result=result,
            source_docs=source_docs,
            session_id=conversation.session_id,
        )

    async def chat_stream(
        self,
        message: str,
        department: Department | None = None,
        session_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        conversation = await self._get_or_create_conversation(session_id, department)
        history_messages = await self._load_recent_history(conversation.id)
        history = [
            {"role": item.role, "content": item.content} for item in history_messages
        ]
        query = self._build_query_with_history(message=message, history=history)

        await self.conversation_repo.add_message(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        yield self._sse({"type": "heartbeat"})

        try:
            result = self.supervisor.route_query(query, department)
        except Exception as exc:
            logger.error("chat_stream_failed", error=str(exc), message=message)
            fallback = {
                "type": "trace",
                "data": {"error": str(exc), "departments": [], "confidence": 0.0},
            }
            yield self._sse(fallback)
            await self.conversation_repo.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content="I couldn't complete your request right now. Please try again.",
                sources=[],
                trace={"error": str(exc), "history_count": len(history)},
            )
            await self.session.commit()
            yield self._sse({"type": "done"})
            return

        tokens = [token for token in result.answer.split(" ") if token]
        for token in tokens:
            yield self._sse({"type": "token", "content": token})

        source_docs = self._extract_sources(result)
        yield self._sse({"type": "sources", "data": source_docs})
        yield self._sse(
            {
                "type": "trace",
                "data": {
                    "departments": [dept.value for dept in result.departments_used],
                    "confidence": result.confidence,
                    "agent_traces": result.agent_traces,
                },
            }
        )

        await self.conversation_repo.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=result.answer,
            sources=source_docs,
            trace={
                "agent_traces": result.agent_traces,
                "confidence": result.confidence,
                "history_count": len(history),
            },
        )
        await self.session.commit()
        yield self._sse({"type": "done"})

    async def _get_or_create_conversation(
        self,
        session_id: str | None,
        department: Department | None,
    ) -> Conversation:
        resolved_session_id = session_id or str(uuid.uuid4())
        default_department = (department or Department.IT_SUPPORT).value
        return await self.conversation_repo.get_or_create_conversation(
            session_id=resolved_session_id,
            department=default_department,
        )

    def _build_query_with_history(
        self,
        *,
        message: str,
        history: list[dict[str, Any]],
    ) -> str:
        if not history:
            return message

        context_lines = [
            f"{entry.get('role', 'unknown')}: {entry.get('content', '')}"
            for entry in history
        ]
        context = "\n".join(context_lines)
        return f"Conversation history:\n{context}\n\nCurrent user message:\n{message}"

    def _extract_sources(self, result: SupervisorResult) -> list[dict[str, Any]]:
        traces = result.agent_traces or []
        extracted: list[dict[str, Any]] = []
        for trace in traces:
            if not isinstance(trace, dict):
                continue
            raw_sources = trace.get("sources")
            if not isinstance(raw_sources, list):
                continue
            for source in raw_sources:
                if not isinstance(source, dict):
                    continue
                extracted.append(
                    {
                        "title": str(source.get("title", "unknown")),
                        "snippet": str(source.get("snippet", "")),
                        "department": str(source.get("department", "")),
                    }
                )
        return extracted

    async def _load_recent_history(self, conversation_id: int) -> list[Message]:
        total_result = await self.session.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        total = int(total_result.scalar_one() or 0)
        offset = max(total - 10, 0)
        return await self.conversation_repo.get_messages(
            conversation_id,
            limit=10,
            offset=offset,
        )

    def _to_chat_response(
        self,
        *,
        result: SupervisorResult,
        source_docs: list[dict[str, Any]],
        session_id: str,
    ) -> ChatResponse:
        departments = [department.value for department in result.departments_used]
        decision = ", ".join(departments) if departments else "unknown"
        source_labels = [item.get("title", "unknown") for item in source_docs]

        trace = AgentTrace(
            supervisor_decision=decision,
            agents_invoked=departments or ["unknown"],
            retrieval_sources=source_docs,
            iterations=max(1, len(result.agent_traces)),
        )
        department = (
            result.departments_used[0]
            if result.departments_used
            else Department.IT_SUPPORT
        )
        return ChatResponse(
            answer=result.answer,
            department=department,
            sources=[str(label) for label in source_labels],
            confidence=float(result.confidence),
            trace=trace,
            session_id=session_id,
        )

    def _sse(self, payload: dict[str, Any]) -> str:
        return f"data: {json.dumps(payload)}\n\n"
