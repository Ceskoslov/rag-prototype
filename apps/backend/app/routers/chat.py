from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.docstore import RedisDocStore
from app.core.embeddings import get_embedding_model
from app.core.llm import get_chat_model
from app.core.settings import settings
from app.models.conversation import Conversation
from app.repositories.conversation import ConversationRepository
from app.repositories.vectorstore import ChromaRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService
from app.services.rag import RAGService
from app.services.retrieval import HybridRetriever

router = APIRouter(prefix="/api/v1", tags=["chat"])


async def get_db() -> Any:
    async for session in get_async_session():
        yield session


@lru_cache(maxsize=1)
def _create_rag_service() -> RAGService:
    llm = get_chat_model()
    chroma_repo = ChromaRepository()
    docstore = RedisDocStore(redis_url=settings.redis_url)
    retriever = HybridRetriever(
        vector_repository=chroma_repo,
        docstore=docstore,
        embedding_model=get_embedding_model(settings),
    )
    return RAGService(llm=llm, retriever=retriever)


async def get_chat_service(session: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(session=session, rag=_create_rag_service())


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return await service.process_message(
        message=request.message,
        knowledge_base=request.knowledge_base,
        session_id=request.session_id,
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    stream = service.chat_stream(
        message=request.message,
        knowledge_base=request.knowledge_base,
        session_id=request.session_id,
    )
    return StreamingResponse(stream, media_type="text/event-stream")


@router.get("/sessions")
async def list_sessions(session: AsyncSession = Depends(get_db)):
    conversations = (
        (
            await session.execute(
                select(Conversation).order_by(Conversation.id.desc()).limit(50)
            )
        )
        .scalars()
        .all()
    )
    return [
        {
            "session_id": item.session_id,
            "knowledge_base": item.knowledge_base,
            "created_at": item.created_at,
        }
        for item in conversations
    ]


@router.get("/sessions/{session_id}/messages")
async def session_messages(session_id: str, session: AsyncSession = Depends(get_db)):
    repository = ConversationRepository(session)
    conversation = await repository.get_conversation(session_id)
    if conversation is None:
        raise HTTPException(404, "Conversation not found")
    messages = await repository.get_messages(conversation.id, limit=500)
    return {
        "session_id": session_id,
        "knowledge_base": conversation.knowledge_base,
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "sources": message.sources or [],
                "trace": message.trace,
            }
            for message in messages
        ],
    }
