#!/usr/bin/env python3
"""Independent retrieval benchmark; --mode rag requires real model providers."""

import argparse
import asyncio
import json
import re
import statistics
import tempfile
import time
from pathlib import Path

import chromadb
from fakeredis import FakeRedis

from app.core.docstore import RedisDocStore
from app.core.embeddings import MockEmbeddings, get_embedding_model
from app.core.llm import get_chat_model
from app.core.settings import settings
from app.repositories.vectorstore import ChromaRepository
from app.services.chunking import ChunkingService
from app.services.evaluation import QATriple, RagasEvaluator
from app.services.ingestion import IngestionService
from app.services.rag import RAGService
from app.services.retrieval import HybridRetriever


async def main():
    root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=root / "benchmarks/cases.json")
    parser.add_argument("--corpus", type=Path, default=root / "benchmarks/corpus")
    parser.add_argument("--mode", choices=["retrieval", "rag"], default="retrieval")
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Call Ragas judges; incurs configured provider charges",
    )
    parser.add_argument("--output", type=Path, default=root / "benchmark-report.json")
    args = parser.parse_args()
    if args.mode == "rag" and (
        settings.llm_provider == "mock" or settings.embedding_provider == "mock"
    ):
        parser.error("RAG quality evaluation requires real LLM and embedding providers")
    if args.judge and args.mode != "rag":
        parser.error("--judge requires --mode rag")
    cases = json.loads(args.cases.read_text())
    embeddings = (
        MockEmbeddings() if args.mode == "retrieval" else get_embedding_model(settings)
    )
    samples = []
    rows = []
    with tempfile.TemporaryDirectory() as path:
        repository = ChromaRepository(chromadb.PersistentClient(path=path))
        store = RedisDocStore(redis_client=FakeRedis(decode_responses=True))
        await IngestionService(
            repository, store, ChunkingService(), embeddings
        ).ingest_all(args.corpus)
        retriever = HybridRetriever(repository, store, embeddings)
        rag = RAGService(get_chat_model(), retriever) if args.mode == "rag" else None
        for case in cases:
            started = time.perf_counter()
            if rag:
                result = await asyncio.to_thread(
                    rag.query, case["question"], case["knowledge_base"]
                )
                sources = result.sources
                answer = result.answer
                if case["reference"] and sources:
                    samples.append(
                        QATriple(
                            case["question"],
                            answer,
                            [source["content"] for source in sources],
                            case["reference"],
                        )
                    )
            else:
                documents = retriever.retrieve(
                    case["question"], case["knowledge_base"], k=6
                )
                sources = RAGService._sources(documents)
                answer = None
            retrieved = [
                (source["knowledge_base"], source["source_path"]) for source in sources
            ]
            expected = {
                (source["knowledge_base"], source["source_path"])
                for source in case["expected_sources"]
            }
            positions = [
                index
                for index, source in enumerate(retrieved, start=1)
                if source in expected
            ]
            citations = [
                int(number) for number in re.findall(r"\[(\d+)\]", answer or "")
            ]
            rows.append(
                {
                    "id": case["id"],
                    "recall_at_6": len(expected.intersection(retrieved)) / len(expected)
                    if expected
                    else None,
                    "reciprocal_rank": 1 / min(positions) if positions else 0,
                    "no_answer": not expected,
                    "abstained": not result.grounded if rag else not sources,
                    "citations_valid": bool(citations)
                    and all(1 <= number <= len(sources) for number in citations)
                    if answer
                    else None,
                    "latency_ms": (time.perf_counter() - started) * 1000,
                    "answer": answer,
                    "sources": retrieved,
                }
            )
    answerable = [row for row in rows if not row["no_answer"]]
    report = {
        "mode": args.mode,
        "quality_claim": args.mode == "rag",
        "provider": settings.llm_provider if rag else "offline_feature_hashing",
        "recall_at_6": statistics.mean(row["recall_at_6"] for row in answerable),
        "mrr": statistics.mean(row["reciprocal_rank"] for row in answerable),
        "latency_p50_ms": statistics.median(row["latency_ms"] for row in rows),
        "rows": rows,
    }
    if args.judge:
        report["ragas"] = await RagasEvaluator().score(samples)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "rows"}, indent=2
        )
    )
    if args.mode == "retrieval" and report["recall_at_6"] < 0.9:
        raise SystemExit("Offline retrieval regression: recall below 0.9")


if __name__ == "__main__":
    asyncio.run(main())
