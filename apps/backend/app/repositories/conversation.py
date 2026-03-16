"""Repository for conversation and message CRUD operations."""

from typing import List, Optional, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    """Repository for managing conversations and messages with async PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_conversation(
        self, session_id: str, department: str
    ) -> Conversation:
        """Create a new conversation."""
        conv = Conversation(session_id=session_id, department=department)
        self.session.add(conv)
        await self.session.flush()
        await self.session.refresh(conv)
        return conv

    async def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """Retrieve conversation by session_id."""
        result = await self.session.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        trace: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Add a message to a conversation."""
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
            trace=trace,
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg

    async def get_messages(
        self, conversation_id: int, limit: int = 100, offset: int = 0
    ) -> List[Message]:
        """Retrieve messages for a conversation with pagination."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_or_create_conversation(
        self, session_id: str, department: str
    ) -> Conversation:
        """Get existing conversation or create new one if not exists."""
        conv = await self.get_conversation(session_id)
        if conv:
            return conv
        return await self.create_conversation(session_id, department)

    async def get_messages_for_context(
        self, conversation_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages formatted for LangChain context.

        Returns list of dicts with 'role' and 'content' keys.
        Orders by most recent, then reverses to chronological.
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.id))
            .limit(limit)
        )
        messages = list(result.scalars().all())

        messages.reverse()

        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def save_agent_response(
        self,
        conversation_id: int,
        response: str,
        trace: Optional[Dict[str, Any]] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        """Save assistant message with sources and trace metadata."""
        return await self.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            sources=sources,
            trace=trace,
        )
