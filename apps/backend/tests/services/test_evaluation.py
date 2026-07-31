from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.evaluation import EvaluationResult
from app.models.message import Message


def _evaluation_scores() -> dict[str, float]:
    return {
        "faithfulness": 0.85,
        "answer_relevancy": 0.9,
        "context_precision": 0.78,
        "context_recall": 0.82,
    }


@pytest.mark.asyncio
async def test_evaluate_conversation_computes_and_stores_metrics(
    async_session_factory_test,
) -> None:
    from app.services.evaluation import EvaluationService

    async with async_session_factory_test() as session:
        conversation = Conversation(
            session_id="eval-session-1", knowledge_base="it_support"
        )
        session.add(conversation)
        await session.flush()
        session.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content="How do I reset my VPN password?",
            )
        )
        session.add(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content="Use the SSO self-service reset page.",
                sources=[{"title": "VPN Guide", "snippet": "Use SSO portal"}],
            )
        )
        await session.commit()

        with patch("app.services.evaluation.AzureChatOpenAI") as mock_azure_llm:
            mock_azure_llm.return_value = MagicMock()
            with patch("app.services.evaluation.evaluate") as mock_ragas_evaluate:
                mock_ragas_evaluate.return_value = _evaluation_scores()

                service = EvaluationService(session=session)
                result = await service.evaluate_conversation("eval-session-1")

        assert result.conversation_id == conversation.id
        assert float(result.faithfulness) == pytest.approx(0.85)
        assert float(result.answer_relevancy) == pytest.approx(0.9)
        assert float(result.context_precision) == pytest.approx(0.78)
        assert float(result.context_recall) == pytest.approx(0.82)

        stored = (
            await session.execute(
                select(EvaluationResult).where(
                    EvaluationResult.conversation_id == conversation.id
                )
            )
        ).scalar_one()

        assert float(stored.faithfulness) == pytest.approx(0.85)
        assert float(stored.answer_relevancy) == pytest.approx(0.9)


@pytest.mark.asyncio
async def test_evaluate_conversation_handles_missing_sources_gracefully(
    async_session_factory_test,
) -> None:
    from app.services.evaluation import EvaluationService

    async with async_session_factory_test() as session:
        conversation = Conversation(session_id="eval-session-2", knowledge_base="legal")
        session.add(conversation)
        await session.flush()
        session.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content="Can I claim compensation?",
            )
        )
        session.add(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content="You may be eligible under EU261.",
                sources=None,
            )
        )
        await session.commit()

        with patch("app.services.evaluation.AzureChatOpenAI") as mock_azure_llm:
            mock_azure_llm.return_value = MagicMock()
            with patch("app.services.evaluation.evaluate") as mock_ragas_evaluate:
                mock_ragas_evaluate.return_value = _evaluation_scores()
                service = EvaluationService(session=session)
                result = await service.evaluate_conversation("eval-session-2")

        assert result is not None
        assert float(result.context_precision) == pytest.approx(0.78)


@pytest.mark.asyncio
async def test_evaluate_conversation_raises_for_missing_conversation(
    async_session_factory_test,
) -> None:
    from app.services.evaluation import EvaluationService

    async with async_session_factory_test() as session:
        service = EvaluationService(session=session)
        with pytest.raises(ValueError, match="Conversation not found"):
            await service.evaluate_conversation("does-not-exist")


@pytest.mark.asyncio
async def test_evaluate_conversation_uses_mocked_ragas_call(
    async_session_factory_test,
) -> None:
    from app.services.evaluation import EvaluationService

    async with async_session_factory_test() as session:
        conversation = Conversation(
            session_id="eval-session-3", knowledge_base="credit_card"
        )
        session.add(conversation)
        await session.flush()
        session.add(
            Message(
                conversation_id=conversation.id, role="user", content="What is APR?"
            )
        )
        session.add(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content="APR is annual percentage rate.",
                sources=[{"title": "Card Terms", "snippet": "APR definition"}],
            )
        )
        await session.commit()

        with patch("app.services.evaluation.AzureChatOpenAI") as mock_azure_llm:
            mock_azure_llm.return_value = MagicMock()
            with patch("app.services.evaluation.evaluate") as mock_ragas_evaluate:
                mock_ragas_evaluate.return_value = _evaluation_scores()
                service = EvaluationService(session=session)
                await service.evaluate_conversation("eval-session-3")

        mock_ragas_evaluate.assert_called_once()
