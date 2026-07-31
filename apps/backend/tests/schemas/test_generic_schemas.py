import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas.chat import ChatRequest
from app.schemas.common import KnowledgeBaseName, normalize_knowledge_base


def test_knowledge_base_names_are_dynamic_and_normalized():
    adapter = TypeAdapter(KnowledgeBaseName)
    assert adapter.validate_python("Product Docs") == "product_docs"
    assert normalize_knowledge_base("hr-policies") == "hr_policies"


def test_invalid_knowledge_base_is_rejected():
    with pytest.raises(ValueError):
        normalize_knowledge_base("../secrets")


def test_chat_request_accepts_legacy_department_alias():
    request = ChatRequest(message="hello", department="legal")
    assert request.knowledge_base == "legal"


def test_chat_request_rejects_empty_message():
    with pytest.raises(ValidationError):
        ChatRequest(message="")
