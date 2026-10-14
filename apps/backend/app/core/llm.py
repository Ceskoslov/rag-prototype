from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from app.core.settings import settings


def get_chat_model() -> BaseChatModel:
    provider = settings.llm_provider.casefold()
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            max_retries=2,
            timeout=45,
            use_responses_api=True,
            store=False,
        )

    if provider == "azure":
        required = {
            "AZURE_OPENAI_ENDPOINT": settings.azure_openai_endpoint,
            "AZURE_OPENAI_API_KEY": settings.azure_openai_api_key,
            "AZURE_OPENAI_DEPLOYMENT_NAME": settings.azure_openai_deployment_name,
            "AZURE_OPENAI_API_VERSION": settings.azure_openai_api_version,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing Azure OpenAI settings: {', '.join(missing)}")
        return AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            azure_deployment=settings.azure_openai_deployment_name,
            api_version=settings.azure_openai_api_version,
            temperature=0,
            max_retries=2,
            timeout=45,
        )

    if provider == "mock":
        return FakeListChatModel(
            responses=[
                (
                    "Mock LLM is enabled. Configure LLM_PROVIDER=openai or azure "
                    "to generate grounded answers."
                )
            ]
        )

    raise ValueError("LLM_PROVIDER must be one of: openai, azure, mock")
