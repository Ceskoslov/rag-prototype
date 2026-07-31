#!/usr/bin/env python3
import argparse
import asyncio
from pathlib import Path

from app.core.docstore import RedisDocStore
from app.core.embeddings import get_embedding_model
from app.core.settings import settings
from app.repositories.vectorstore import ChromaRepository
from app.services.chunking import ChunkingService
from app.services.ingestion import IngestionService


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest local files into one or more RAG knowledge bases"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--knowledge-base", help="Directory name below --data-dir")
    group.add_argument("--all", action="store_true", help="Ingest every directory")
    parser.add_argument("--data-dir", type=Path, default=settings.data_dir)
    args = parser.parse_args()

    service = IngestionService(
        chroma_repo=ChromaRepository(),
        docstore=RedisDocStore(redis_url=settings.redis_url),
        chunking_service=ChunkingService(),
        embedding_model=get_embedding_model(settings),
    )
    if args.all:
        results = await service.ingest_all(args.data_dir)
    else:
        count = await service.ingest_knowledge_base(
            args.knowledge_base,
            args.data_dir,
        )
        results = {args.knowledge_base: count}

    for name, processed in results.items():
        print(f"{name}: {processed} changed file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
