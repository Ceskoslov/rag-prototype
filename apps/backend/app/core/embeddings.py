import os

from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
from pydantic import SecretStr

_EMBEDDING_MODEL_CACHE: dict[str, Embeddings] = {}


def _get_setting_value(settings: object, *keys: str) -> str | None:
    for key in keys:
        value = getattr(settings, key, None)
        if value is None:
            continue
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
    return None


def clear_embedding_model_cache() -> None:
    _EMBEDDING_MODEL_CACHE.clear()


def get_embedding_model(settings: object) -> Embeddings:
    provider = _get_setting_value(settings, "embedding_provider", "EMBEDDING_PROVIDER")
    if provider is None:
        provider = os.getenv("EMBEDDING_PROVIDER")
    normalized_provider = (provider or "").lower()

    if normalized_provider in _EMBEDDING_MODEL_CACHE:
        return _EMBEDDING_MODEL_CACHE[normalized_provider]

    if normalized_provider == "local":
        model = HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-base-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        _EMBEDDING_MODEL_CACHE[normalized_provider] = model
        return model

    if normalized_provider == "azure":
        azure_deployment = _get_setting_value(
            settings,
            "azure_openai_embedding_deployment",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            "azure_openai_deployment",
            "AZURE_OPENAI_DEPLOYMENT",
        )
        if azure_deployment is None:
            azure_deployment = os.getenv(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
            ) or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        azure_endpoint = _get_setting_value(
            settings,
            "azure_openai_endpoint",
            "AZURE_OPENAI_ENDPOINT",
        )
        if azure_endpoint is None:
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = _get_setting_value(
            settings,
            "azure_openai_api_key",
            "AZURE_OPENAI_API_KEY",
        )
        if api_key is None:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")

        model = AzureOpenAIEmbeddings(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_key=SecretStr(api_key) if api_key is not None else None,
        )
        _EMBEDDING_MODEL_CACHE[normalized_provider] = model
        return model

    raise ValueError(f"Invalid embedding provider: {provider}")
