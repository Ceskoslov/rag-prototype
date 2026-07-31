from langchain_core.documents import Document

from app.services.retrieval import HybridRetriever


def test_reciprocal_rank_fusion_combines_dense_and_lexical_rankings():
    first = Document(id="a", page_content="alpha", metadata={})
    second = Document(id="b", page_content="beta", metadata={})

    fused = HybridRetriever._reciprocal_rank_fusion(
        vector_docs=[first, second],
        lexical_docs=[second, first],
    )

    assert {document.id for document in fused} == {"a", "b"}
    assert all(document.metadata["retrieval_score"] > 0 for document in fused)
