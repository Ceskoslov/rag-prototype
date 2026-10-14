import asyncio

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk

from app.services.rag import RAGService
from tests.services.test_rag import StubRetriever


class StreamingModel:
    async def astream(self, messages):
        yield AIMessageChunk(content="退款")
        await asyncio.sleep(0)
        yield AIMessageChunk(
            content="三十天 [1]",
            usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        )

    async def ainvoke(self, messages):
        return AIMessage(content='{"status":"approved","confidence":0.9}')


@pytest.mark.asyncio
async def test_stream_emits_model_chunks_before_result():
    events = [
        event
        async for event in RAGService(StreamingModel(), StubRetriever()).astream(
            "退款期限？"
        )
    ]
    assert [event["content"] for event in events if event["type"] == "token"] == [
        "退款",
        "三十天 [1]",
    ]
    result = events[-1]["data"]
    assert events[-1]["type"] == "result"
    assert result.answer == "退款三十天 [1]"
    assert result.grounded
    assert result.metrics["tokens"]["total_tokens"] == 15
    assert result.metrics["first_token_ms"] is not None
    assert [stage["stage"] for stage in result.metrics["stages"]] == [
        "retrieve",
        "generate",
        "critique",
    ]


@pytest.mark.asyncio
async def test_cancellation_closes_model_stream():
    closed = asyncio.Event()

    class BlockingModel(StreamingModel):
        async def astream(self, messages):
            try:
                yield AIMessageChunk(content="first")
                await asyncio.Event().wait()
            finally:
                closed.set()

    async def consume():
        async for _ in RAGService(BlockingModel(), StubRetriever()).astream("test"):
            pass

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert closed.is_set()
