from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.supervisor import create_supervisor_service
from app.core.database import get_async_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService

router = APIRouter(prefix="/api/v1", tags=["chat"])


async def get_db() -> Any:
    async for session in get_async_session():
        yield session


class NullRetriever:
    def invoke(self, query: str, config: dict[str, Any] | None = None) -> list[Any]:
        _ = (query, config)
        return []


def _default_supervisor() -> Any:
    llm = FakeListChatModel(responses=["Acknowledged."])
    retriever = NullRetriever()
    return create_supervisor_service(llm=llm, retriever=retriever)


async def get_chat_service(session: AsyncSession = Depends(get_db)) -> ChatService:
    supervisor = _default_supervisor()
    return ChatService(session=session, supervisor=supervisor)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return await service.process_message(
        message=request.message,
        department=request.department,
        session_id=request.session_id,
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    stream = service.chat_stream(
        message=request.message,
        department=request.department,
        session_id=request.session_id,
    )
    return StreamingResponse(stream, media_type="text/event-stream")
