from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from contextlib import aclosing, suppress
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation import ConversationRepository
from app.schemas.chat import AgentTrace, ChatResponse
from app.services.rag import RAGResult, RAGService

logger = get_logger(__name__)


class ChatService:
    def __init__(self, session: AsyncSession, rag: RAGService | Any):
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.rag = rag

    async def process_message(
        self,
        message: str,
        knowledge_base: str | None = None,
        session_id: str | None = None,
    ) -> ChatResponse:
        conversation = await self._get_or_create_conversation(
            session_id,
            knowledge_base,
        )
        history = await self._history(conversation.id)
        query = await self.rag.resolve_question(message, history)
        result = await self._run_rag(query, knowledge_base)

        await self.conversation_repo.add_message(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        await self.conversation_repo.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=result.answer,
            sources=result.sources,
            trace=self._trace_payload(result, len(history)),
        )
        await self.session.commit()
        return self._to_chat_response(result, conversation.session_id)

    async def chat_stream(
        self,
        message: str,
        knowledge_base: str | None = None,
        session_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        conversation = await self._get_or_create_conversation(
            session_id,
            knowledge_base,
        )
        history = await self._history(conversation.id)
        yield self._sse({"type": "heartbeat"})
        query = await self.rag.resolve_question(message, history)
        await self.conversation_repo.add_message(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        yield self._sse({"type": "heartbeat"})

        queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=64)

        async def produce():
            try:
                async with aclosing(self.rag.astream(query, knowledge_base)) as stream:
                    async for event in stream:
                        await queue.put(event)
            except Exception as exc:
                await queue.put(exc)
            finally:
                if not asyncio.current_task().cancelling():
                    await queue.put(None)

        producer = asyncio.create_task(produce())
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=10)
                except TimeoutError:
                    yield self._sse({"type": "heartbeat"})
                    continue
                if event is None:
                    break
                if isinstance(event, Exception):
                    logger.exception("rag_stream_failed", error=str(event))
                    yield self._sse(
                        {
                            "type": "error",
                            "data": {
                                "message": "Unable to complete this answer. Please retry."
                            },
                        }
                    )
                    return
                if event["type"] != "result":
                    yield self._sse(event)
                    continue
                result = event["data"]
                await self.conversation_repo.add_message(
                    conversation.id,
                    "assistant",
                    result.answer,
                    sources=result.sources,
                    trace=self._trace_payload(result, len(history)),
                )
                await self.session.commit()
                yield self._sse({"type": "reset", "content": result.answer})
                yield self._sse({"type": "sources", "data": result.sources})
                yield self._sse(
                    {"type": "trace", "data": self._agent_trace(result).model_dump()}
                )
                yield self._sse(
                    {
                        "type": "done",
                        "data": {
                            "session_id": conversation.session_id,
                            "grounded": result.grounded,
                        },
                    }
                )
        finally:
            producer.cancel()
            with suppress(asyncio.CancelledError):
                await producer

    async def _run_rag(
        self,
        query: str,
        knowledge_base: str | None,
    ) -> RAGResult:
        try:
            return await self.rag.aquery(query, knowledge_base)
        except Exception as exc:
            logger.exception(
                "rag_query_failed",
                error=str(exc),
                knowledge_base=knowledge_base,
            )
            return RAGResult(
                answer="I couldn't complete your request right now. Please try again.",
                knowledge_bases_used=[],
                sources=[],
                confidence=0.0,
                iterations=0,
                pipeline_steps=["error"],
            )

    async def _get_or_create_conversation(
        self,
        session_id: str | None,
        knowledge_base: str | None,
    ) -> Conversation:
        return await self.conversation_repo.get_or_create_conversation(
            session_id=session_id or str(uuid.uuid4()),
            knowledge_base=knowledge_base or "all",
        )

    async def _history(self, conversation_id: int) -> list[dict[str, str]]:
        messages = await self._load_recent_history(conversation_id)
        return [{"role": item.role, "content": item.content} for item in messages]

    @staticmethod
    def _build_query_with_history(
        *,
        message: str,
        history: list[dict[str, Any]],
    ) -> str:
        if not history:
            return message
        context = "\n".join(
            f"{entry.get('role', 'unknown')}: {entry.get('content', '')}"
            for entry in history
        )
        return (
            "Use this conversation history only to resolve references in the current "
            f"question:\n{context}\n\nCurrent question:\n{message}"
        )

    async def _load_recent_history(self, conversation_id: int) -> list[Message]:
        total_result = await self.session.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        total = int(total_result.scalar_one() or 0)
        return await self.conversation_repo.get_messages(
            conversation_id,
            limit=10,
            offset=max(total - 10, 0),
        )

    @staticmethod
    def _agent_trace(result: RAGResult) -> AgentTrace:
        return AgentTrace(
            knowledge_bases_searched=result.knowledge_bases_used,
            retrieval_sources=result.sources,
            iterations=result.iterations,
            pipeline_steps=result.pipeline_steps,
            metrics=result.metrics,
            grounded=result.grounded,
        )

    def _trace_payload(
        self,
        result: RAGResult,
        history_count: int,
    ) -> dict[str, Any]:
        return {
            **self._agent_trace(result).model_dump(),
            "confidence": result.confidence,
            "history_count": history_count,
        }

    def _to_chat_response(
        self,
        result: RAGResult,
        session_id: str,
    ) -> ChatResponse:
        return ChatResponse(
            answer=result.answer,
            knowledge_bases=result.knowledge_bases_used,
            sources=[str(item["title"]) for item in result.sources],
            confidence=result.confidence,
            trace=self._agent_trace(result),
            session_id=session_id,
        )

    @staticmethod
    def _sse(payload: dict[str, Any]) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
