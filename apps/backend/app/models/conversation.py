"""Conversation model for storing conversation sessions."""

from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.evaluation import EvaluationResult


class Conversation(Base):
    """Long-term memory storage for conversation sessions."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    department: Mapped[str] = mapped_column(String(255))

    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="select",
    )
    evaluation_results: Mapped[List["EvaluationResult"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, session_id={self.session_id}, department={self.department})>"
