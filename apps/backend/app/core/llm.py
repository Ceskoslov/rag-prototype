from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_openai import AzureChatOpenAI

from app.core.settings import settings


def get_chat_model() -> BaseChatModel:
    azure_endpoint = settings.azure_openai_endpoint
    azure_api_key = settings.azure_openai_api_key
    azure_deployment = settings.azure_openai_deployment_name

    if azure_endpoint and azure_api_key and azure_deployment:
        return AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            azure_deployment=azure_deployment,
            api_version=settings.azure_openai_api_version,
            temperature=0,
            max_retries=2,
        )

    return FakeListChatModel(responses=["Acknowledged."])
