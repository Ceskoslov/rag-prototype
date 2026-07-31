from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from langchain_openai import AzureChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.evaluation import EvaluationResult
from app.repositories.conversation import ConversationRepository


def evaluate(*args: Any, **kwargs: Any) -> Any:
    ragas_module = importlib.import_module("ragas")
    evaluate_fn = ragas_module.evaluate
    return evaluate_fn(*args, **kwargs)


@dataclass
class QATriple:
    question: str
    answer: str
    contexts: list[str]


class EvaluationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversation_repo = ConversationRepository(session)

    async def evaluate_conversation(self, session_id: str) -> EvaluationResult:
        conversation = await self.conversation_repo.get_conversation(session_id)
        if conversation is None:
            raise ValueError(f"Conversation not found for session_id={session_id}")

        messages = await self.conversation_repo.get_messages(conversation.id, limit=500)
        triples = self._extract_qa_triples(messages)
        if not triples:
            raise ValueError(f"No evaluable QA pairs found for session_id={session_id}")

        metrics = self._compute_ragas_metrics(triples)

        existing = (
            await self.session.execute(
                select(EvaluationResult).where(
                    EvaluationResult.conversation_id == conversation.id
                )
            )
        ).scalar_one_or_none()

        if existing is None:
            record = EvaluationResult(
                conversation_id=conversation.id,
                faithfulness=metrics["faithfulness"],
                answer_relevancy=metrics["answer_relevancy"],
                context_precision=metrics["context_precision"],
                context_recall=metrics["context_recall"],
            )
            self.session.add(record)
        else:
            record = existing
            record.faithfulness = metrics["faithfulness"]
            record.answer_relevancy = metrics["answer_relevancy"]
            record.context_precision = metrics["context_precision"]
            record.context_recall = metrics["context_recall"]

        await self.session.commit()
        await self.session.refresh(record)
        return record

    def _extract_qa_triples(self, messages: list[Any]) -> list[QATriple]:
        triples: list[QATriple] = []
        pending_question: str | None = None

        for msg in messages:
            role = getattr(msg, "role", "")
            content = str(getattr(msg, "content", "") or "").strip()
            if not content:
                continue

            if role == "user":
                pending_question = content
                continue

            if role != "assistant" or pending_question is None:
                continue

            raw_sources = getattr(msg, "sources", None)
            contexts = self._extract_contexts(raw_sources)
            triples.append(
                QATriple(
                    question=pending_question,
                    answer=content,
                    contexts=contexts,
                )
            )
            pending_question = None

        return triples

    def _extract_contexts(self, raw_sources: Any) -> list[str]:
        if not raw_sources:
            return [""]

        contexts: list[str] = []
        if isinstance(raw_sources, list):
            for source in raw_sources:
                if isinstance(source, dict):
                    snippet = source.get("snippet") or source.get("content") or ""
                    title = source.get("title") or ""
                    text = " - ".join(
                        [part for part in [title, snippet] if part]
                    ).strip()
                    if text:
                        contexts.append(text)

        return contexts or [""]

    def _compute_ragas_metrics(self, triples: list[QATriple]) -> dict[str, float]:
        payload = {
            "question": [t.question for t in triples],
            "answer": [t.answer for t in triples],
            "contexts": [t.contexts for t in triples],
            "ground_truth": [t.answer for t in triples],
        }

        try:
            datasets_module = importlib.import_module("datasets")
            dataset_class = datasets_module.Dataset
            dataset: Any = dataset_class.from_dict(payload)
        except Exception:
            dataset = payload

        try:
            metrics_module = importlib.import_module("ragas.metrics")
            selected_metrics = [
                metrics_module.faithfulness,
                metrics_module.answer_relevancy,
                metrics_module.context_precision,
                metrics_module.context_recall,
            ]
        except Exception:
            selected_metrics = [
                "faithfulness",
                "answer_relevancy",
                "context_precision",
                "context_recall",
            ]

        llm = AzureChatOpenAI(
            azure_endpoint=getattr(settings, "azure_openai_endpoint", None),
            api_key=getattr(settings, "azure_openai_api_key", None),
            azure_deployment=getattr(settings, "azure_openai_deployment_name", None),
            api_version=getattr(settings, "azure_openai_api_version", None),
        )

        result = evaluate(
            dataset,
            metrics=selected_metrics,
            llm=llm,
        )

        return {
            "faithfulness": float(result["faithfulness"]),
            "answer_relevancy": float(result["answer_relevancy"]),
            "context_precision": float(result["context_precision"]),
            "context_recall": float(result["context_recall"]),
        }
