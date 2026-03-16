from types import SimpleNamespace
from typing import cast

import pytest
from pydantic import SecretStr

from app.core import embeddings


@pytest.fixture(autouse=True)
def clear_embedding_cache():
    embeddings.clear_embedding_model_cache()
    yield
    embeddings.clear_embedding_model_cache()


def test_get_embedding_model_local_returns_bge_with_required_config(
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    class FakeBgeEmbeddings:
        def __init__(
            self,
            model_name: str,
            model_kwargs: dict[str, str],
            encode_kwargs: dict[str, bool],
        ) -> None:
            captured["model_name"] = model_name
            captured["model_kwargs"] = model_kwargs
            captured["encode_kwargs"] = encode_kwargs

    monkeypatch.setattr(embeddings, "HuggingFaceBgeEmbeddings", FakeBgeEmbeddings)

    settings = SimpleNamespace(embedding_provider="local")
    model = embeddings.get_embedding_model(settings)

    assert isinstance(model, FakeBgeEmbeddings)
    assert captured["model_name"] == "BAAI/bge-base-en-v1.5"
    assert captured["model_kwargs"] == {"device": "cpu"}
    assert captured["encode_kwargs"] == {"normalize_embeddings": True}


def test_get_embedding_model_azure_returns_azure_with_required_config(
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    class FakeAzureEmbeddings:
        def __init__(
            self,
            azure_deployment: str,
            azure_endpoint: str,
            api_key: SecretStr,
        ) -> None:
            captured["azure_deployment"] = azure_deployment
            captured["azure_endpoint"] = azure_endpoint
            captured["api_key"] = api_key

    monkeypatch.setattr(embeddings, "AzureOpenAIEmbeddings", FakeAzureEmbeddings)

    settings = SimpleNamespace(
        embedding_provider="azure",
        azure_openai_embedding_deployment="embed-deployment",
        azure_openai_endpoint="https://example.openai.azure.com",
        azure_openai_api_key="test-key",
    )
    model = embeddings.get_embedding_model(settings)

    assert isinstance(model, FakeAzureEmbeddings)
    assert captured["azure_deployment"] == "embed-deployment"
    assert captured["azure_endpoint"] == "https://example.openai.azure.com"
    captured_api_key = cast(SecretStr, captured["api_key"])
    assert captured_api_key.get_secret_value() == "test-key"


def test_get_embedding_model_returns_singleton_per_provider(
    monkeypatch: pytest.MonkeyPatch,
):
    class FakeBgeEmbeddings:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    class FakeAzureEmbeddings:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    monkeypatch.setattr(embeddings, "HuggingFaceBgeEmbeddings", FakeBgeEmbeddings)
    monkeypatch.setattr(embeddings, "AzureOpenAIEmbeddings", FakeAzureEmbeddings)

    local_settings = SimpleNamespace(embedding_provider="local")
    azure_settings = SimpleNamespace(
        embedding_provider="azure",
        azure_openai_embedding_deployment="embed-deployment",
        azure_openai_endpoint="https://example.openai.azure.com",
        azure_openai_api_key="test-key",
    )

    local_first = embeddings.get_embedding_model(local_settings)
    local_second = embeddings.get_embedding_model(local_settings)
    azure_first = embeddings.get_embedding_model(azure_settings)
    azure_second = embeddings.get_embedding_model(azure_settings)

    assert local_first is local_second
    assert azure_first is azure_second
    assert local_first is not azure_first


def test_embedding_dimensions_match_expected_provider_output(
    monkeypatch: pytest.MonkeyPatch,
):
    class FakeBgeEmbeddings:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def embed_query(self, _text: str) -> list[float]:
            return [0.1] * 768

    class FakeAzureEmbeddings:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def embed_query(self, _text: str) -> list[float]:
            return [0.2] * 1536

    monkeypatch.setattr(embeddings, "HuggingFaceBgeEmbeddings", FakeBgeEmbeddings)
    monkeypatch.setattr(embeddings, "AzureOpenAIEmbeddings", FakeAzureEmbeddings)

    local_settings = SimpleNamespace(embedding_provider="local")
    azure_settings = SimpleNamespace(
        embedding_provider="azure",
        azure_openai_embedding_deployment="embed-deployment",
        azure_openai_endpoint="https://example.openai.azure.com",
        azure_openai_api_key="test-key",
    )

    local_model = embeddings.get_embedding_model(local_settings)
    azure_model = embeddings.get_embedding_model(azure_settings)
    local_vector = local_model.embed_query("hello")
    azure_vector = azure_model.embed_query("hello")

    assert isinstance(local_vector, list)
    assert isinstance(azure_vector, list)
    assert all(isinstance(value, float) for value in local_vector)
    assert all(isinstance(value, float) for value in azure_vector)
    assert len(local_vector) == 768
    assert len(azure_vector) == 1536


def test_get_embedding_model_invalid_provider_raises_value_error():
    settings = SimpleNamespace(embedding_provider="unknown")

    with pytest.raises(ValueError, match="Invalid embedding provider"):
        _ = embeddings.get_embedding_model(settings)
