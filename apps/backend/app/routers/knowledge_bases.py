from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

import arq
from arq.connections import RedisSettings
from arq.jobs import Job
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.docstore import RedisDocStore
from app.core.settings import settings
from app.repositories.vectorstore import ChromaRepository
from app.schemas.common import normalize_knowledge_base
from app.services.documents import DocumentService

router = APIRouter(prefix="/api/v1", tags=["knowledge-bases"])


class KnowledgeBaseSummary(BaseModel):
    name: str
    document_chunks: int
    index_version: str | None = None


def get_document_service() -> DocumentService:
    return DocumentService(
        settings.data_dir, ChromaRepository(), RedisDocStore(settings.redis_url)
    )


async def get_job_pool():
    pool = await arq.create_pool(
        RedisSettings.from_dsn(
            settings.arq_redis_url or settings.redis_url.rsplit("/", 1)[0] + "/1"
        )
    )
    try:
        yield pool
    finally:
        await pool.aclose()


def _name(value: str) -> str:
    try:
        return normalize_knowledge_base(value)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


async def _enqueue(pool: Any, knowledge_base: str) -> dict:
    job = await pool.enqueue_job(
        "ingest_knowledge_base_task",
        knowledge_base,
        _job_id=f"ingest:{knowledge_base}:{uuid.uuid4().hex}",
    )
    if job is None:
        raise HTTPException(503, "Unable to queue indexing; retry rebuild")
    return {"job_id": job.job_id, "status": "queued", "knowledge_base": knowledge_base}


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseSummary])
def list_knowledge_bases(service: DocumentService = Depends(get_document_service)):
    repository = service.repository
    names = set(repository.list_knowledge_bases())
    if service.data_dir.exists():
        names.update(
            path.name
            for path in service.data_dir.iterdir()
            if path.is_dir() and not path.is_symlink()
        )
    items = []
    for name in sorted(names):
        _name(name)
        try:
            collection = repository.get_collection(name)
            items.append(
                KnowledgeBaseSummary(
                    name=name,
                    document_chunks=collection.count(),
                    index_version=collection.name,
                )
            )
        except ValueError:
            items.append(KnowledgeBaseSummary(name=name, document_chunks=0))
    return items


@router.get("/knowledge-bases/{knowledge_base}/documents")
def list_documents(
    knowledge_base: str, service: DocumentService = Depends(get_document_service)
):
    try:
        return service.list_documents(_name(knowledge_base))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/knowledge-bases/{knowledge_base}/rebuild", status_code=202)
async def rebuild(knowledge_base: str, pool=Depends(get_job_pool)):
    return await _enqueue(pool, _name(knowledge_base))


@router.put(
    "/knowledge-bases/{knowledge_base}/documents/{source_path:path}", status_code=202
)
async def upload_document(
    knowledge_base: str,
    source_path: str,
    request: Request,
    service: DocumentService = Depends(get_document_service),
    pool=Depends(get_job_pool),
):
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(413, "Documents must be at most 20 MB")
    if not content:
        raise HTTPException(422, "Document is empty")
    name = _name(knowledge_base)
    try:
        await asyncio.to_thread(service.write, name, source_path, bytes(content))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return await _enqueue(pool, name)


@router.delete(
    "/knowledge-bases/{knowledge_base}/documents/{source_path:path}", status_code=202
)
async def delete_document(
    knowledge_base: str,
    source_path: str,
    service: DocumentService = Depends(get_document_service),
    pool=Depends(get_job_pool),
):
    name = _name(knowledge_base)
    try:
        await asyncio.to_thread(service.delete, name, source_path)
    except FileNotFoundError as exc:
        raise HTTPException(404, "Document not found") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return await _enqueue(pool, name)


@router.get("/knowledge-bases/{knowledge_base}/documents/{source_path:path}")
def download_document(
    knowledge_base: str,
    source_path: str,
    service: DocumentService = Depends(get_document_service),
):
    try:
        path = service.file_path(_name(knowledge_base), source_path)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not path.is_file():
        raise HTTPException(404, "Document not found")
    return FileResponse(
        path,
        filename=path.name,
        media_type="application/octet-stream",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.get("/jobs/{job_id}")
async def job_status(job_id: str, pool=Depends(get_job_pool)):
    job = Job(job_id, pool)
    status = await job.status()
    value = getattr(status, "value", str(status))
    result = None
    if value == "complete":
        info = await job.result_info()
        if info and not info.success:
            value = "failed"
            result = {"error": "Indexing failed; check worker logs and retry rebuild"}
        elif info:
            result = info.result
    if value == "not_found":
        raise HTTPException(404, "Job expired or not found")
    progress = await pool.get(f"job_progress:{job_id}")
    return {
        "job_id": job_id,
        "status": value,
        "result": result,
        "progress": json.loads(progress) if progress else None,
    }
