from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.repositories.vectorstore import ChromaRepository

router = APIRouter(prefix="/api/v1", tags=["knowledge-bases"])


class KnowledgeBaseSummary(BaseModel):
    name: str
    document_chunks: int


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseSummary])
def list_knowledge_bases() -> list[KnowledgeBaseSummary]:
    repository = ChromaRepository()
    return [
        KnowledgeBaseSummary(
            name=name,
            document_chunks=repository.get_collection(name).count(),
        )
        for name in repository.list_knowledge_bases()
    ]
