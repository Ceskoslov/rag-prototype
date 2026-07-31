from pathlib import Path

from app.services.ingestion import IngestionService


def test_discovers_arbitrary_knowledge_base_directories(tmp_path: Path):
    (tmp_path / "product_docs").mkdir()
    (tmp_path / "product_docs" / "guide.md").write_text("hello")
    (tmp_path / "hr_policies").mkdir()
    (tmp_path / "hr_policies" / "leave.pdf").write_bytes(b"not parsed here")
    (tmp_path / "empty").mkdir()

    assert IngestionService.discover_knowledge_bases(tmp_path) == [
        "hr_policies",
        "product_docs",
    ]


def test_loads_json_as_searchable_text(tmp_path: Path):
    file_path = tmp_path / "config.json"
    file_path.write_text('{"retention_days": 30}', encoding="utf-8")

    documents = IngestionService._load_file(
        file_path=file_path,
        knowledge_base="policies",
        source_path="config.json",
    )

    assert "retention_days" in documents[0].page_content
    assert documents[0].metadata["knowledge_base"] == "policies"
