from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.supervisor import create_supervisor_service
from app.core.database import get_async_session
from app.core.docstore import RedisDocStore
from app.core.embeddings import get_embedding_model
from app.core.llm import get_chat_model
from app.core.settings import settings
from app.repositories.vectorstore import ChromaRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService
from app.services.retrieval import HybridRetriever

router = APIRouter(prefix="/api/v1", tags=["chat"])


async def get_db() -> Any:
    async for session in get_async_session():
        yield session


def _create_supervisor() -> Any:
    llm = get_chat_model()
    chroma_repo = ChromaRepository()
    docstore = RedisDocStore(redis_url=settings.redis_url)
    retriever = HybridRetriever(vector_repository=chroma_repo, docstore=docstore)
    return create_supervisor_service(llm=llm, retriever=retriever)


async def get_chat_service(session: AsyncSession = Depends(get_db)) -> ChatService:
    supervisor = _create_supervisor()
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
