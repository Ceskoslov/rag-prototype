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
            '{"status":"approved","confidence":0.95}',
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


def test_rejected_answers_finish_three_iterations_and_abstain():
    llm = FakeListChatModel(
        responses=[
            "Unsupported answer [1]",
            '{"status":"rejected","confidence":0.1}',
            "rewritten",
        ]
    )
    result = RAGService(llm, StubRetriever()).query("refund window?")
    assert result.iterations == 3
    assert result.confidence == 0
    assert not result.grounded
    assert "verified evidence" in result.answer


def test_multiple_passages_from_same_file_keep_citation_ids():
    docs = StubRetriever().invoke("question") * 2
    sources = RAGService._sources(docs)
    assert [source["citation_id"] for source in sources] == [1, 2]
    assert sources[0]["content"] == docs[0].page_content


def test_critique_receives_evidence_and_invalid_citations_are_rejected():
    from langchain_core.messages import AIMessage

    class RecordingModel:
        def __init__(self):
            self.prompts = []

        def invoke(self, messages):
            prompt = messages[-1].content
            self.prompts.append(prompt)
            return AIMessage(
                content='{"status":"approved","confidence":0.99}'
                if "Return ONLY JSON" in prompt
                else "30 days [99]"
            )

    llm = RecordingModel()
    result = RAGService(llm, StubRetriever()).query("refund?")
    assert not result.grounded
    assert all(
        "The refund window is 30 days." in prompt
        for prompt in llm.prompts
        if "Return ONLY JSON" in prompt
    )
