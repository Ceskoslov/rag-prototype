from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.evaluation import EvaluationResult
from app.repositories.conversation import ConversationRepository


@dataclass
class QATriple:
    question: str
    answer: str
    contexts: list[str]
    reference: str | None = None


class RagasEvaluator:
    """Ragas 0.4 collections adapter; imports are optional until evaluation runs."""

    async def score(self, triples: list[QATriple]) -> dict[str, float | None]:
        if settings.llm_provider == "mock":
            raise ValueError("Mock providers cannot produce meaningful quality metrics")
        from openai import AsyncAzureOpenAI, AsyncOpenAI
        from ragas.embeddings.base import embedding_factory
        from ragas.llms import llm_factory
        from ragas.metrics.collections import (
            AnswerRelevancy,
            ContextPrecisionWithoutReference,
            ContextPrecisionWithReference,
            ContextRecall,
            Faithfulness,
        )

        if settings.llm_provider == "azure":
            client = AsyncAzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
                timeout=45,
                max_retries=2,
            )
            model = settings.evaluation_model or settings.azure_openai_deployment_name
            embedding_model = settings.azure_openai_embedding_deployment
            if not model or not embedding_model:
                raise ValueError(
                    "Azure evaluation requires chat and embedding deployments"
                )
        elif settings.llm_provider == "openai":
            client = AsyncOpenAI(
                api_key=settings.openai_api_key, timeout=45, max_retries=2
            )
            model = settings.evaluation_model or settings.openai_model
            embedding_model = settings.openai_embedding_model
        else:
            raise ValueError("Evaluation requires an OpenAI or Azure provider")

        async with client:
            llm = llm_factory(model, client=client)
            embeddings = embedding_factory(
                "openai", model=embedding_model, client=client, interface="modern"
            )
            faithfulness = Faithfulness(llm=llm)
            relevancy = AnswerRelevancy(llm=llm, embeddings=embeddings)
            precision_with = ContextPrecisionWithReference(llm=llm)
            precision_without = ContextPrecisionWithoutReference(llm=llm)
            recall = ContextRecall(llm=llm)
            values: dict[str, list[float]] = {
                name: []
                for name in [
                    "faithfulness",
                    "answer_relevancy",
                    "context_precision",
                    "context_recall",
                ]
            }
            for triple in triples:
                shared = {
                    "user_input": triple.question,
                    "retrieved_contexts": triple.contexts,
                }
                values["faithfulness"].append(
                    float(
                        (
                            await faithfulness.ascore(**shared, response=triple.answer)
                        ).value
                    )
                )
                values["answer_relevancy"].append(
                    float(
                        (
                            await relevancy.ascore(
                                user_input=triple.question, response=triple.answer
                            )
                        ).value
                    )
                )
                if triple.reference:
                    values["context_precision"].append(
                        float(
                            (
                                await precision_with.ascore(
                                    **shared, reference=triple.reference
                                )
                            ).value
                        )
                    )
                    values["context_recall"].append(
                        float(
                            (
                                await recall.ascore(
                                    **shared, reference=triple.reference
                                )
                            ).value
                        )
                    )
                else:
                    values["context_precision"].append(
                        float(
                            (
                                await precision_without.ascore(
                                    **shared, response=triple.answer
                                )
                            ).value
                        )
                    )
            result = {
                name: sum(scores) / len(scores) if scores else None
                for name, scores in values.items()
            }
            if any(
                value is not None and (not math.isfinite(value) or not 0 <= value <= 1)
                for value in result.values()
            ):
                raise ValueError("Evaluator returned invalid metrics")
            return result


class EvaluationService:
    def __init__(self, session: AsyncSession, evaluator: Any = None):
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.evaluator = evaluator or RagasEvaluator()

    async def evaluate_conversation(
        self, session_id: str, references: dict[str, str] | None = None
    ) -> EvaluationResult:
        conversation = await self.conversation_repo.get_conversation(session_id)
        if conversation is None:
            raise ValueError(f"Conversation not found for session_id={session_id}")
        messages = await self.conversation_repo.get_messages(conversation.id, limit=500)
        triples = self._extract_qa_triples(messages, references or {})
        if not triples:
            raise ValueError(
                "No evaluable QA pairs with complete evidence; start a new conversation after indexing"
            )
        metrics = await self.evaluator.score(triples)
        record = (
            await self.session.execute(
                select(EvaluationResult).where(
                    EvaluationResult.conversation_id == conversation.id
                )
            )
        ).scalar_one_or_none()
        if record is None:
            record = EvaluationResult(conversation_id=conversation.id)
            self.session.add(record)
        for name, value in metrics.items():
            setattr(record, name, value)
        record.details = {
            "provider": settings.llm_provider,
            "model": settings.evaluation_model or settings.openai_model
            if settings.llm_provider == "openai"
            else settings.evaluation_model or settings.azure_openai_deployment_name,
            "sample_count": len(triples),
            "reference_count": sum(triple.reference is not None for triple in triples),
            "context_precision_basis": "reference"
            if all(triple.reference for triple in triples)
            else "response_or_reference",
            "contexts": "complete_passages",
        }
        await self.session.commit()
        await self.session.refresh(record)
        return record

    @staticmethod
    def _extract_qa_triples(
        messages: list[Any], references: dict[str, str]
    ) -> list[QATriple]:
        triples = []
        pending = None
        for message in messages:
            if message.role == "user":
                pending = message.content
            elif message.role == "assistant" and pending:
                contexts = [
                    source["content"]
                    for source in (message.sources or [])
                    if isinstance(source, dict) and source.get("content")
                ]
                if contexts and len(contexts) == len(message.sources or []):
                    triples.append(
                        QATriple(
                            pending, message.content, contexts, references.get(pending)
                        )
                    )
                pending = None
        return triples
