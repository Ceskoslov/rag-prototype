import pytest
from typing import cast
from langchain_core.documents import Document

from app.schemas.common import Department
from app.services.chunking import ChunkingService


def _metadata(chunk: Document) -> dict[str, object]:
    return cast(dict[str, object], chunk.metadata)


def _meta_str(chunk: Document, key: str) -> str:
    value = _metadata(chunk)[key]
    assert isinstance(value, str)
    return value


def _meta_int(chunk: Document, key: str) -> int:
    value = _metadata(chunk)[key]
    assert isinstance(value, int)
    return value


@pytest.fixture
def markdown_doc() -> Document:
    content = """
# Password Reset Procedures

## Overview
SkyWing Airlines uses a unified Single Sign-On system for corporate resources. This section explains the high-level process and policy context for account recovery.

## Password Requirements
Minimum 14 characters with uppercase, lowercase, numeric, and special characters. Password reuse is blocked for the last 12 passwords. Rotation happens every 90 days.

## Self-Service Password Reset
Employees use the SSPR portal and complete identity verification. After verification, a new compliant password can be set.

## Manual Reset via Help Desk
When SSPR cannot be used, employees call the help desk and complete identity verification. A temporary password is issued and must be changed at next login.

## VPN and Mobile Sync
After password changes, users must update credentials in VPN clients and mobile mail apps to avoid authentication failures.

## Account Lockout
Five failed attempts trigger lockout. Account recovery and unlock procedures are available through secure support channels.

""" + ("Security policy details and remediation workflow. " * 180)

    return Document(
        page_content=content,
        metadata={
            "department": Department.IT_SUPPORT,
            "source_file": "password-reset.md",
        },
    )


def test_chunk_document_returns_parent_and_child_chunks(markdown_doc: Document):
    service = ChunkingService()

    chunks = service.chunk_document(markdown_doc)

    assert len(chunks) > 0
    chunk_types = {_meta_str(chunk, "chunk_type") for chunk in chunks}
    assert "parent" in chunk_types
    assert "child" in chunk_types


def test_parent_chunks_are_approximately_1000_tokens(markdown_doc: Document):
    service = ChunkingService()

    chunks = service.chunk_document(markdown_doc)
    parent_chunks = [
        chunk for chunk in chunks if _meta_str(chunk, "chunk_type") == "parent"
    ]

    assert len(parent_chunks) > 0
    assert all(len(chunk.page_content) <= 1200 for chunk in parent_chunks)
    assert any(len(chunk.page_content) >= 500 for chunk in parent_chunks)


def test_child_chunks_are_approximately_200_tokens(markdown_doc: Document):
    service = ChunkingService()

    chunks = service.chunk_document(markdown_doc)
    child_chunks = [
        chunk for chunk in chunks if _meta_str(chunk, "chunk_type") == "child"
    ]

    assert len(child_chunks) > 0
    assert all(len(chunk.page_content) <= 260 for chunk in child_chunks)
    assert any(len(chunk.page_content) >= 100 for chunk in child_chunks)


def test_child_chunks_reference_parent_id(markdown_doc: Document):
    service = ChunkingService()

    chunks = service.chunk_document(markdown_doc)
    parent_chunks = [
        chunk for chunk in chunks if _meta_str(chunk, "chunk_type") == "parent"
    ]
    child_chunks = [
        chunk for chunk in chunks if _meta_str(chunk, "chunk_type") == "child"
    ]

    parent_ids = {chunk.id for chunk in parent_chunks}

    assert len(parent_ids) > 0
    assert all(_meta_str(child, "parent_id") in parent_ids for child in child_chunks)


def test_metadata_propagates_to_all_chunks(markdown_doc: Document):
    service = ChunkingService()

    chunks = service.chunk_document(markdown_doc)

    assert len(chunks) > 0
    for chunk in chunks:
        assert _meta_str(chunk, "department") == Department.IT_SUPPORT.value
        assert _meta_str(chunk, "source_file") == "password-reset.md"
        assert _meta_str(chunk, "chunk_type") in {"parent", "child"}
        _ = _meta_int(chunk, "chunk_index")
        metadata = _metadata(chunk)
        if _meta_str(chunk, "chunk_type") == "child":
            assert "parent_id" in metadata
        else:
            assert "parent_id" not in metadata
