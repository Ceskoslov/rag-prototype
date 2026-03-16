from datetime import datetime

from pydantic import BaseModel, Field


class RAGASMetrics(BaseModel):
    """RAGAS evaluation metrics."""

    faithfulness: float = Field(..., description="Faithfulness metric (0-1)")
    answer_relevancy: float = Field(..., description="Answer relevancy metric (0-1)")
    context_precision: float = Field(..., description="Context precision metric (0-1)")
    context_recall: float = Field(..., description="Context recall metric (0-1)")


class EvaluationRequest(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID to evaluate")


class EvaluationResult(BaseModel):
    conversation_id: str = Field(..., description="Evaluated conversation ID")
    metrics: RAGASMetrics = Field(..., description="RAGAS metrics")
    evaluated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Evaluation timestamp"
    )


class EvaluationTriggerRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to evaluate")


class EvaluationTriggerResponse(BaseModel):
    job_id: str
    session_id: str


class EvaluationResultResponse(BaseModel):
    session_id: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    created_at: datetime


class EvaluationStatusResponse(BaseModel):
    session_id: str
    status: str
    job_id: str | None = None
