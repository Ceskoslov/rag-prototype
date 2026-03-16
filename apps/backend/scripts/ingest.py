#!/usr/bin/env python3
import argparse
import asyncio
import sys
from pathlib import Path

from app.core.docstore import RedisDocStore
from app.core.embeddings import get_embedding_model
from app.core.settings import Settings
from app.repositories.vectorstore import ChromaRepository
from app.schemas.common import Department
from app.services.chunking import ChunkingService
from app.services.ingestion import IngestionService


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest Markdown documents into ChromaDB and Redis docstore"
    )
    parser.add_argument(
        "--department",
        choices=["it_support", "legal", "credit_card", "airport_ground"],
        help="Department to ingest (e.g., it_support)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ingest all departments",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Base data directory (default: data/)",
    )

    args = parser.parse_args()

    if not args.department and not args.all:
        parser.error("Either --department or --all is required")

    if args.department and args.all:
        parser.error("Cannot specify both --department and --all")

    data_dir = args.data_dir
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
        return 1

    settings = Settings()

    chroma_repo = ChromaRepository()
    docstore = RedisDocStore(redis_url=settings.redis_url)
    chunking_service = ChunkingService()
    embedding_model = get_embedding_model(settings)

    ingestion_service = IngestionService(
        chroma_repo=chroma_repo,
        docstore=docstore,
        chunking_service=chunking_service,
        embedding_model=embedding_model,
    )

    if args.all:
        departments = [
            Department.IT_SUPPORT,
            Department.LEGAL,
            Department.CREDIT_CARD,
            Department.AIRPORT_GROUND,
        ]
        print(f"Ingesting all departments: {[d.value for d in departments]}")
    else:
        departments = [Department(args.department)]
        print(f"Ingesting department: {args.department}")

    for department in departments:
        print(f"\n=== Processing {department.value} ===")
        try:
            await ingestion_service.ingest_department(
                department=department,
                data_dir=data_dir,
            )
            print(f"✓ Successfully ingested {department.value}")
        except Exception as e:
            print(f"✗ Error ingesting {department.value}: {e}", file=sys.stderr)
            return 1

    print("\n=== Ingestion Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
