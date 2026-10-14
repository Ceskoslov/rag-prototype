from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from pydantic import SecretStr

_EMBEDDING_MODEL_CACHE: dict[tuple[str, str], Embeddings] = {}


def clear_embedding_model_cache() -> None:
    _EMBEDDING_MODEL_CACHE.clear()


def get_embedding_model(settings: object) -> Embeddings:
    provider = str(getattr(settings, "embedding_provider", "local")).casefold()

    if provider == "mock":
        return MockEmbeddings()

    if provider == "local":
        from langchain_huggingface import HuggingFaceEmbeddings

        model_name = str(
            getattr(settings, "embedding_model_name", "BAAI/bge-m3")
        )
        cache_key = (provider, model_name)
        if cache_key not in _EMBEDDING_MODEL_CACHE:
            _EMBEDDING_MODEL_CACHE[cache_key] = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        return _EMBEDDING_MODEL_CACHE[cache_key]

    if provider == "openai":
        model_name = str(
            getattr(settings, "openai_embedding_model", "text-embedding-3-small")
        )
        api_key = getattr(settings, "openai_api_key", None)
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai"
            )
        cache_key = (provider, model_name)
        if cache_key not in _EMBEDDING_MODEL_CACHE:
            _EMBEDDING_MODEL_CACHE[cache_key] = OpenAIEmbeddings(
                model=model_name,
                api_key=SecretStr(str(api_key)),
            )
        return _EMBEDDING_MODEL_CACHE[cache_key]

    if provider == "azure":
        deployment = getattr(settings, "azure_openai_embedding_deployment", None)
        endpoint = getattr(settings, "azure_openai_endpoint", None)
        api_key = getattr(settings, "azure_openai_api_key", None)
        if not all((deployment, endpoint, api_key)):
            raise ValueError(
                "Azure endpoint, key, and embedding deployment are required "
                "when EMBEDDING_PROVIDER=azure"
            )
        cache_key = (provider, str(deployment))
        if cache_key not in _EMBEDDING_MODEL_CACHE:
            _EMBEDDING_MODEL_CACHE[cache_key] = AzureOpenAIEmbeddings(
                azure_deployment=str(deployment),
                azure_endpoint=str(endpoint),
                api_key=SecretStr(str(api_key)),
            )
        return _EMBEDDING_MODEL_CACHE[cache_key]

    raise ValueError("EMBEDDING_PROVIDER must be one of: local, openai, azure, mock")


class MockEmbeddings(Embeddings):
    """Deterministic feature hashing for offline wiring checks, not quality evals."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        import hashlib
        import math
        import re

        vector = [0.0] * 64
        for token in re.findall(r"\w+", text.casefold()):
            digest = hashlib.sha256(token.encode()).digest()
            vector[int.from_bytes(digest[:2]) % 64] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
