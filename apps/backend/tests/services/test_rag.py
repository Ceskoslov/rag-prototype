from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.services.rag import RAGService


class StubRetriever:
    def invoke(self, query, config=None):
        return [
            Document(
                page_content="The refund window is 30 days.",
                metadata={
                    "knowledge_base": "policies",
                    "source_path": "refunds.md",
                    "retrieval_score": 0.9,
                },
            )
        ]


def test_rag_service_is_domain_agnostic():
    llm = FakeListChatModel(
        responses=[
            "The refund window is 30 days [1].",
            "approved confidence: 0.95",
        ]
    )

    result = RAGService(llm=llm, retriever=StubRetriever()).query(
        "How long is the refund window?",
        knowledge_base="policies",
    )

    assert result.answer == "The refund window is 30 days [1]."
    assert result.knowledge_bases_used == ["policies"]
    assert result.sources[0]["title"] == "refunds.md"
    assert result.confidence == 0.95
