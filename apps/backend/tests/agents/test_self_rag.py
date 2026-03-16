from __future__ import annotations

from typing import Any

from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.agents.self_rag import create_self_rag_graph


class FakeRetriever:
    def __init__(self, mapping: dict[str, list[Document]]) -> None:
        self.mapping = mapping
        self.calls: list[str] = []

    def invoke(
        self, query: str, config: dict[str, Any] | None = None
    ) -> list[Document]:
        _ = config
        self.calls.append(query)
        return self.mapping.get(query, self.mapping.get("default", []))


def test_good_answer_approved_in_one_iteration() -> None:
    retriever = FakeRetriever(
        {
            "vpn": [
                Document(page_content="Reset password then reconnect VPN.", metadata={})
            ]
        }
    )
    llm = FakeListChatModel(
        responses=["Follow reset flow and MFA.", "approved\nconfidence: 0.91"]
    )

    graph = create_self_rag_graph(llm=llm, retriever=retriever)
    result = graph.invoke({"query": "vpn", "department": "it_support"})

    assert result["iterations"] == 1
    assert result["critique_result"] == "approved"
    assert float(result["confidence"]) > 0.7


def test_bad_answer_triggers_exactly_3_iterations() -> None:
    retriever = FakeRetriever(
        {
            "weak": [Document(page_content="weak context", metadata={})],
            "weak improved": [Document(page_content="still weak", metadata={})],
            "weak improved improved": [
                Document(page_content="third weak", metadata={})
            ],
        }
    )
    llm = FakeListChatModel(
        responses=[
            "bad-1",
            "rejected\nconfidence: 0.2",
            "weak improved",
            "bad-2",
            "rejected\nconfidence: 0.18",
            "weak improved improved",
            "bad-3",
            "rejected\nconfidence: 0.1",
        ]
    )

    graph = create_self_rag_graph(llm=llm, retriever=retriever)
    result = graph.with_config(recursion_limit=14).invoke(
        {"query": "weak", "department": "it_support"}
    )

    assert result["iterations"] == 3
    assert result["critique_result"] == "rejected"
    assert float(result["confidence"]) < 0.5


def test_unanswerable_query_returns_no_information_response() -> None:
    retriever = FakeRetriever({"default": []})
    llm = FakeListChatModel(responses=["unused"])

    graph = create_self_rag_graph(llm=llm, retriever=retriever)
    result = graph.invoke({"query": "missing", "department": "legal"})

    assert "I don't have information" in result["generation"]
    assert result["critique_result"] == "approved"


def test_no_infinite_loop_remaining_steps_enforced() -> None:
    retriever = FakeRetriever(
        {
            "loop": [Document(page_content="one", metadata={})],
            "loop refined": [Document(page_content="two", metadata={})],
        }
    )
    llm = FakeListChatModel(
        responses=[
            "bad",
            "rejected\nconfidence: 0.1",
            "loop refined",
            "bad",
            "rejected\nconfidence: 0.1",
            "loop refined",
            "bad",
            "rejected\nconfidence: 0.1",
        ]
    )

    graph = create_self_rag_graph(llm=llm, retriever=retriever)
    result = graph.with_config(recursion_limit=14).invoke(
        {"query": "loop", "department": "it_support"}
    )

    assert result["iterations"] == 3
    assert len(result["node_history"]) <= 11


def test_retrieve_generate_critique_refine_cycle_order() -> None:
    retriever = FakeRetriever(
        {
            "q": [Document(page_content="d1", metadata={})],
            "q refined": [Document(page_content="d2", metadata={})],
        }
    )
    llm = FakeListChatModel(
        responses=[
            "ans-1",
            "rejected\nconfidence: 0.4",
            "q refined",
            "ans-2",
            "approved\nconfidence: 0.82",
        ]
    )

    graph = create_self_rag_graph(llm=llm, retriever=retriever)
    result = graph.with_config(recursion_limit=14).invoke(
        {"query": "q", "department": "it_support"}
    )

    assert result["iterations"] == 2
    assert result["node_history"] == [
        "retrieve",
        "generate",
        "critique",
        "rewrite_query",
        "retrieve",
        "generate",
        "critique",
    ]
    assert retriever.calls == ["q", "q refined"]
