from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.conversation import Conversation
from app.models.message import Message
from app.services.evaluation import EvaluationService, RagasEvaluator


@pytest.mark.asyncio
async def test_evaluation_uses_independent_reference_and_full_context(
    async_session_factory_test,
):
    full_context = "Refund policy " * 100
    async with async_session_factory_test() as session:
        conversation = Conversation(session_id="eval-full", knowledge_base="policies")
        session.add(conversation)
        await session.flush()
        session.add_all(
            [
                Message(
                    conversation_id=conversation.id,
                    role="user",
                    content="Refund window?",
                ),
                Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content="60 days [1]",
                    sources=[{"content": full_context, "snippet": "short"}],
                ),
            ]
        )
        await session.commit()
        evaluator = SimpleNamespace(
            score=AsyncMock(
                return_value={
                    "faithfulness": 0.1,
                    "answer_relevancy": 0.8,
                    "context_precision": 0.5,
                    "context_recall": 0.7,
                }
            )
        )
        result = await EvaluationService(session, evaluator).evaluate_conversation(
            "eval-full", {"Refund window?": "30 days"}
        )
        sample = evaluator.score.call_args.args[0][0]
        assert sample.reference == "30 days"
        assert sample.answer == "60 days [1]"
        assert sample.contexts == [full_context]
        assert result.details["reference_count"] == 1
        assert float(result.faithfulness) == pytest.approx(0.1)


@pytest.mark.asyncio
async def test_missing_reference_is_not_replaced_with_generated_answer(
    async_session_factory_test,
):
    async with async_session_factory_test() as session:
        conversation = Conversation(
            session_id="eval-no-reference", knowledge_base="policies"
        )
        session.add(conversation)
        await session.flush()
        session.add_all(
            [
                Message(
                    conversation_id=conversation.id, role="user", content="Question"
                ),
                Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content="Answer",
                    sources=[{"content": "Evidence"}],
                ),
            ]
        )
        await session.commit()
        evaluator = SimpleNamespace(
            score=AsyncMock(
                return_value={
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.8,
                    "context_precision": 0.7,
                    "context_recall": None,
                }
            )
        )
        result = await EvaluationService(session, evaluator).evaluate_conversation(
            "eval-no-reference"
        )
        assert evaluator.score.call_args.args[0][0].reference is None
        assert result.context_recall is None
        assert result.details["reference_count"] == 0


def test_legacy_snippets_are_not_treated_as_complete_evidence():
    samples = EvaluationService._extract_qa_triples(
        [
            SimpleNamespace(role="user", content="Question"),
            SimpleNamespace(
                role="assistant", content="Answer", sources=[{"snippet": "Short"}]
            ),
        ],
        {},
    )
    assert samples == []


@pytest.mark.asyncio
async def test_mock_evaluator_does_not_manufacture_quality_scores(monkeypatch):
    from app.core.settings import settings

    monkeypatch.setattr(settings, "llm_provider", "mock")
    with pytest.raises(ValueError, match="meaningful quality"):
        await RagasEvaluator().score([])


@pytest.mark.asyncio
async def test_missing_conversation(async_session_factory_test):
    async with async_session_factory_test() as session:
        with pytest.raises(ValueError, match="Conversation not found"):
            await EvaluationService(session).evaluate_conversation("unknown")
