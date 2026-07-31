"""Conversation model for storing conversation sessions."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.evaluation import EvaluationResult
    from app.models.message import Message


class Conversation(Base):
    """Long-term memory storage for conversation sessions."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Keep the physical column name for existing databases while exposing
    # domain-neutral terminology throughout the application.
    knowledge_base: Mapped[str] = mapped_column("department", String(255))

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="select",
    )
    evaluation_results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Conversation(id={self.id}, session_id={self.session_id}, "
            f"knowledge_base={self.knowledge_base})>"
        )
