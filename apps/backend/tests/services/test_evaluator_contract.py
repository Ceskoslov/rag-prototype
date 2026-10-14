"""Exercise the real Ragas 0.4 factories without making a provider request."""

from importlib.util import find_spec

import pytest

from app.core.settings import settings
from app.services.evaluation import RagasEvaluator


@pytest.mark.asyncio
async def test_ragas_collections_factory_contract(monkeypatch):
    if find_spec("ragas") is None:
        pytest.skip("Optional evaluation extra is not installed")
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "not-a-real-key")
    monkeypatch.setattr(settings, "evaluation_model", "gpt-5.6-luna")
    result = await RagasEvaluator().score([])
    assert result == {
        "faithfulness": None,
        "answer_relevancy": None,
        "context_precision": None,
        "context_recall": None,
    }
