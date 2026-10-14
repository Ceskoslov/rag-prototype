from types import SimpleNamespace

from app.core.embeddings import get_embedding_model


def test_offline_embeddings_are_deterministic_and_normalized():
    model = get_embedding_model(SimpleNamespace(embedding_provider="mock"))
    vector = model.embed_query("refund policy")
    assert vector == model.embed_documents(["refund policy"])[0]
    assert len(vector) == 64
    assert abs(sum(value * value for value in vector) - 1) < 1e-8
    assert vector != model.embed_query("vpn password")
