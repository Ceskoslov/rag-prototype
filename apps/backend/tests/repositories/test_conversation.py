"""Test suite for ConversationRepository."""

import pytest
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation import ConversationRepository


@pytest.mark.asyncio
async def test_create_conversation(async_session_factory_test):
    """Test creating a new conversation."""
    async with async_session_factory_test() as session:
        repo = ConversationRepository(session)

        conv = await repo.create_conversation(
            session_id="test-session-1", knowledge_base="it_support"
        )

        assert conv.id is not None
        assert conv.session_id == "test-session-1"
        assert conv.knowledge_base == "it_support"

        # Verify it's in the database
        result = await session.execute(
            select(Conversation).where(Conversation.session_id == "test-session-1")
        )
        db_conv = result.scalar_one()
        assert db_conv.id == conv.id


@pytest.mark.asyncio
async def test_get_conversation(async_session_factory_test):
    """Test retrieving an existing conversation."""
    async with async_session_factory_test() as session:
        # Create a conversation first
        conv = Conversation(session_id="test-session-2", knowledge_base="legal")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        # Now test get_conversation
        repo = ConversationRepository(session)
        retrieved = await repo.get_conversation("test-session-2")

        assert retrieved is not None
        assert retrieved.id == conv.id
        assert retrieved.session_id == "test-session-2"
        assert retrieved.knowledge_base == "legal"


@pytest.mark.asyncio
async def test_get_conversation_not_found(async_session_factory_test):
    """Test retrieving a non-existent conversation returns None."""
    async with async_session_factory_test() as session:
        repo = ConversationRepository(session)
        result = await repo.get_conversation("nonexistent-session")

        assert result is None


@pytest.mark.asyncio
async def test_add_message(async_session_factory_test):
    """Test adding a message to a conversation."""
    async with async_session_factory_test() as session:
        # Create a conversation first
        conv = Conversation(session_id="test-session-3", knowledge_base="credit_card")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        # Add a message
        repo = ConversationRepository(session)
        msg = await repo.add_message(
            conversation_id=conv.id,
            role="user",
            content="What is my credit limit?",
            sources={"documents": ["doc1", "doc2"]},
            trace={"agent": "credit_card", "iterations": 1},
        )

        assert msg.id is not None
        assert msg.conversation_id == conv.id
        assert msg.role == "user"
        assert msg.content == "What is my credit limit?"
        assert msg.sources == {"documents": ["doc1", "doc2"]}
        assert msg.trace == {"agent": "credit_card", "iterations": 1}


@pytest.mark.asyncio
async def test_get_messages(async_session_factory_test):
    """Test retrieving messages with limit and offset."""
    async with async_session_factory_test() as session:
        # Create conversation and multiple messages
        conv = Conversation(session_id="test-session-4", knowledge_base="it_support")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        # Add 5 messages
        for i in range(5):
            msg = Message(
                conversation_id=conv.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
            )
            session.add(msg)
        await session.commit()

        # Test get_messages with limit
        repo = ConversationRepository(session)
        messages = await repo.get_messages(conv.id, limit=3)

        assert len(messages) == 3
        assert messages[0].content == "Message 0"
        assert messages[1].content == "Message 1"
        assert messages[2].content == "Message 2"

        # Test with offset
        messages_offset = await repo.get_messages(conv.id, limit=2, offset=2)
        assert len(messages_offset) == 2
        assert messages_offset[0].content == "Message 2"
        assert messages_offset[1].content == "Message 3"


@pytest.mark.asyncio
async def test_get_or_create_conversation_new(async_session_factory_test):
    """Test get_or_create creates new conversation when not exists."""
    async with async_session_factory_test() as session:
        repo = ConversationRepository(session)

        conv = await repo.get_or_create_conversation(
            session_id="test-session-5", knowledge_base="airport_ground"
        )

        assert conv.id is not None
        assert conv.session_id == "test-session-5"
        assert conv.knowledge_base == "airport_ground"

        # Verify it's in database
        result = await session.execute(
            select(Conversation).where(Conversation.session_id == "test-session-5")
        )
        assert result.scalar_one() is not None


@pytest.mark.asyncio
async def test_get_or_create_conversation_existing(async_session_factory_test):
    """Test get_or_create returns existing conversation without duplicating."""
    async with async_session_factory_test() as session:
        # Create existing conversation
        existing = Conversation(session_id="test-session-6", knowledge_base="legal")
        session.add(existing)
        await session.commit()
        await session.refresh(existing)

        repo = ConversationRepository(session)

        # Call get_or_create with same session_id
        conv = await repo.get_or_create_conversation(
            session_id="test-session-6", knowledge_base="legal"
        )

        assert conv.id == existing.id
        assert conv.session_id == "test-session-6"

        # Verify no duplicate was created
        result = await session.execute(
            select(Conversation).where(Conversation.session_id == "test-session-6")
        )
        all_convs = result.scalars().all()
        assert len(all_convs) == 1


@pytest.mark.asyncio
async def test_get_messages_for_context(async_session_factory_test):
    """Test get_messages_for_context returns recent messages formatted for LangChain."""
    async with async_session_factory_test() as session:
        # Create conversation and messages
        conv = Conversation(session_id="test-session-7", knowledge_base="it_support")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        # Add 15 messages
        for i in range(15):
            msg = Message(
                conversation_id=conv.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
            )
            session.add(msg)
        await session.commit()

        # Test with default limit (10)
        repo = ConversationRepository(session)
        context = await repo.get_messages_for_context(conv.id)

        assert len(context) == 10
        # Should get messages 5-14 (last 10)
        assert context[0]["content"] == "Message 5"
        assert context[0]["role"] == "assistant"
        assert context[-1]["content"] == "Message 14"
        assert context[-1]["role"] == "user"

        # Test with custom limit
        context_limited = await repo.get_messages_for_context(conv.id, limit=5)
        assert len(context_limited) == 5
        assert context_limited[0]["content"] == "Message 10"


@pytest.mark.asyncio
async def test_save_agent_response(async_session_factory_test):
    """Test save_agent_response saves assistant message with sources and trace."""
    async with async_session_factory_test() as session:
        # Create conversation
        conv = Conversation(session_id="test-session-8", knowledge_base="credit_card")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        # Save agent response
        repo = ConversationRepository(session)
        msg = await repo.save_agent_response(
            conversation_id=conv.id,
            response="Your credit limit is $5000.",
            trace={
                "agent": "credit_card",
                "iterations": 2,
                "steps": ["retrieve", "rewrite", "retrieve"],
            },
            sources=[
                {"doc_id": "doc1", "chunk_id": 1},
                {"doc_id": "doc2", "chunk_id": 5},
            ],
        )

        assert msg.id is not None
        assert msg.conversation_id == conv.id
        assert msg.role == "assistant"
        assert msg.content == "Your credit limit is $5000."
        assert msg.trace == {
            "agent": "credit_card",
            "iterations": 2,
            "steps": ["retrieve", "rewrite", "retrieve"],
        }
        assert msg.sources == [
            {"doc_id": "doc1", "chunk_id": 1},
            {"doc_id": "doc2", "chunk_id": 5},
        ]


@pytest.mark.asyncio
async def test_full_conversation_lifecycle(async_session_factory_test):
    """Test complete conversation lifecycle: create, add messages, retrieve context."""
    async with async_session_factory_test() as session:
        repo = ConversationRepository(session)

        # 1. Create or get conversation
        conv = await repo.get_or_create_conversation(
            session_id="lifecycle-session", knowledge_base="it_support"
        )
        assert conv.id is not None

        # 2. Add user message
        user_msg = await repo.add_message(
            conversation_id=conv.id, role="user", content="How do I reset my password?"
        )
        assert user_msg.id is not None

        # 3. Save agent response
        agent_msg = await repo.save_agent_response(
            conversation_id=conv.id,
            response="You can reset your password by clicking 'Forgot Password' on the login page.",
            trace={"agent": "it_support", "iterations": 1},
            sources=[{"doc_id": "it_kb_001"}],
        )
        assert agent_msg.id is not None

        # 4. Add another user message
        await repo.add_message(
            conversation_id=conv.id, role="user", content="Thank you!"
        )

        # 5. Get messages for context
        context = await repo.get_messages_for_context(conv.id, limit=10)
        assert len(context) == 3
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "How do I reset my password?"
        assert context[1]["role"] == "assistant"
        assert context[2]["role"] == "user"
        assert context[2]["content"] == "Thank you!"

        # 6. Verify get_or_create doesn't duplicate
        conv2 = await repo.get_or_create_conversation(
            session_id="lifecycle-session", knowledge_base="it_support"
        )
        assert conv2.id == conv.id
