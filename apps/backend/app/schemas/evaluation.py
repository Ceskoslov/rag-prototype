"""Evaluation and RAGAS metrics schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RAGASMetrics(BaseModel):
    """RAGAS evaluation metrics."""

    faithfulness: float = Field(..., description="Faithfulness metric (0-1)")
    answer_relevancy: float = Field(..., description="Answer relevancy metric (0-1)")
    context_precision: float = Field(..., description="Context precision metric (0-1)")
    context_recall: float = Field(..., description="Context recall metric (0-1)")


class EvaluationRequest(BaseModel):
    """Request to evaluate a conversation."""

    conversation_id: str = Field(..., description="Conversation ID to evaluate")


class EvaluationResult(BaseModel):
    """Result of RAGAS evaluation."""

    conversation_id: str = Field(..., description="Evaluated conversation ID")
    metrics: RAGASMetrics = Field(..., description="RAGAS metrics")
    evaluated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Evaluation timestamp"
    )
