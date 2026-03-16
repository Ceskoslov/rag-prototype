"""EvaluationResult model for storing RAG evaluation metrics."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class EvaluationResult(Base):
    """Evaluation metrics for RAG conversation quality."""

    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    faithfulness: Mapped[float] = mapped_column(Numeric(precision=5, scale=4))
    answer_relevancy: Mapped[float] = mapped_column(Numeric(precision=5, scale=4))
    context_precision: Mapped[float] = mapped_column(Numeric(precision=5, scale=4))
    context_recall: Mapped[float] = mapped_column(Numeric(precision=5, scale=4))

    conversation: Mapped["Conversation"] = relationship(
        back_populates="evaluation_results"
    )

    def __repr__(self) -> str:
        return f"<EvaluationResult(id={self.id}, conversation_id={self.conversation_id}, faithfulness={self.faithfulness})>"
