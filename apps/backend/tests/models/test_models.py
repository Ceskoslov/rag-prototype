"""Test suite for database models."""

import pytest
from datetime import datetime
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.evaluation import EvaluationResult


@pytest.mark.asyncio
async def test_conversation_creation(async_session_factory_test):
    """Test creating a Conversation model."""
    async with async_session_factory_test() as session:
        conv = Conversation(session_id="test-session-1", department="it_support")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        assert conv.id is not None
        assert conv.session_id == "test-session-1"
        assert conv.department == "it_support"
        assert isinstance(conv.created_at, datetime)
        assert isinstance(conv.updated_at, datetime)


@pytest.mark.asyncio
async def test_message_creation(async_session_factory_test):
    """Test creating a Message model."""
    async with async_session_factory_test() as session:
        conv = Conversation(session_id="test-session-2", department="it_support")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        msg = Message(
            conversation_id=conv.id, role="user", content="Hello, how can I help?"
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)

        assert msg.id is not None
        assert msg.conversation_id == conv.id
        assert msg.role == "user"
        assert msg.content == "Hello, how can I help?"
        assert msg.sources is None
        assert msg.trace is None
        assert isinstance(msg.created_at, datetime)


@pytest.mark.asyncio
async def test_message_with_sources_and_trace(async_session_factory_test):
    """Test Message with JSON sources and trace."""
    async with async_session_factory_test() as session:
        conv = Conversation(session_id="test-session-3", department="billing")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        sources = [{"doc_id": "1", "text": "billing info"}]
        trace = {"step": 1, "action": "retrieve"}

        msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Here is your billing info",
            sources=sources,
            trace=trace,
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)

        assert msg.sources == sources
        assert msg.trace == trace


@pytest.mark.asyncio
async def test_evaluation_result_creation(async_session_factory_test):
    """Test creating an EvaluationResult model."""
    async with async_session_factory_test() as session:
        conv = Conversation(session_id="test-session-4", department="technical")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        eval_result = EvaluationResult(
            conversation_id=conv.id,
            faithfulness=0.95,
            answer_relevancy=0.87,
            context_precision=0.92,
            context_recall=0.89,
        )
        session.add(eval_result)
        await session.commit()
        await session.refresh(eval_result)

        assert eval_result.id is not None
        assert eval_result.conversation_id == conv.id
        assert float(eval_result.faithfulness) == 0.95
        assert float(eval_result.answer_relevancy) == 0.87
        assert float(eval_result.context_precision) == 0.92
        assert float(eval_result.context_recall) == 0.89
        assert isinstance(eval_result.created_at, datetime)


@pytest.mark.asyncio
async def test_conversation_message_relationship(async_session_factory_test):
    """Test bidirectional relationship between Conversation and Message."""
    async with async_session_factory_test() as session:
        conv = Conversation(session_id="test-session-5", department="it_support")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        msg1 = Message(conversation_id=conv.id, role="user", content="First message")
        msg2 = Message(conversation_id=conv.id, role="assistant", content="Response")
        session.add(msg1)
        session.add(msg2)
        await session.commit()
        await session.refresh(conv, ["messages"])

        assert len(conv.messages) == 2
        assert msg1 in conv.messages
        assert msg2 in conv.messages

        await session.refresh(msg1, ["conversation"])
        assert msg1.conversation.id == conv.id
        assert msg1.conversation.session_id == "test-session-5"


@pytest.mark.asyncio
async def test_message_cascade_delete(async_session_factory_test):
    """Test that deleting Conversation cascades to Messages."""
    async with async_session_factory_test() as session:
        conv = Conversation(session_id="test-session-6", department="hr")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)
        conv_id = conv.id

        msg = Message(conversation_id=conv.id, role="user", content="Test cascade")
        session.add(msg)
        await session.commit()

        await session.delete(conv)
        await session.commit()

        result = await session.execute(
            select(Message).where(Message.conversation_id == conv_id)
        )
        remaining_messages = result.scalars().all()
        assert len(remaining_messages) == 0


@pytest.mark.asyncio
async def test_evaluation_cascade_delete(async_session_factory_test):
    """Test that deleting Conversation cascades to EvaluationResult."""
    async with async_session_factory_test() as session:
        conv = Conversation(session_id="test-session-7", department="sales")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)
        conv_id = conv.id

        eval_result = EvaluationResult(
            conversation_id=conv.id,
            faithfulness=0.8,
            answer_relevancy=0.75,
            context_precision=0.85,
            context_recall=0.80,
        )
        session.add(eval_result)
        await session.commit()

        await session.delete(conv)
        await session.commit()

        result = await session.execute(
            select(EvaluationResult).where(EvaluationResult.conversation_id == conv_id)
        )
        remaining_evals = result.scalars().all()
        assert len(remaining_evals) == 0


@pytest.mark.asyncio
async def test_message_role_validation(async_session_factory_test):
    """Test Message role is one of allowed values."""
    async with async_session_factory_test() as session:
        conv = Conversation(session_id="test-session-8", department="support")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        valid_roles = ["user", "assistant", "system"]
        for role in valid_roles:
            msg = Message(
                conversation_id=conv.id, role=role, content=f"Message as {role}"
            )
            session.add(msg)

        await session.commit()
        await session.refresh(conv, ["messages"])
        assert len(conv.messages) == 3


@pytest.mark.asyncio
async def test_multiple_evaluation_results_per_conversation(async_session_factory_test):
    """Test multiple EvaluationResults can be associated with one Conversation."""
    async with async_session_factory_test() as session:
        conv = Conversation(session_id="test-session-9", department="finance")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        eval1 = EvaluationResult(
            conversation_id=conv.id,
            faithfulness=0.9,
            answer_relevancy=0.85,
            context_precision=0.88,
            context_recall=0.87,
        )
        eval2 = EvaluationResult(
            conversation_id=conv.id,
            faithfulness=0.92,
            answer_relevancy=0.88,
            context_precision=0.90,
            context_recall=0.89,
        )
        session.add(eval1)
        session.add(eval2)
        await session.commit()

        result = await session.execute(
            select(EvaluationResult).where(EvaluationResult.conversation_id == conv.id)
        )
        evals = result.scalars().all()
        assert len(evals) == 2
