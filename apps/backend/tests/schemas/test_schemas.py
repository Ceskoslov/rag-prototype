"""
Comprehensive Pydantic v2 schema tests for chat, documents, evaluation, and common types.
Tests cover validation, serialization, and all required fields.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.chat import ChatRequest, ChatResponse, ChatStreamEvent, AgentTrace
from app.schemas.document import (
    DocumentChunk,
    DocumentMetadata,
    IngestionRequest,
    IngestionResult,
)
from app.schemas.evaluation import EvaluationRequest, EvaluationResult, RAGASMetrics
from app.schemas.common import Department, HealthResponse, ErrorResponse


class TestDepartmentEnum:
    """Test Department enum has all required values."""

    def test_all_departments_present(self):
        """Verify all 4 departments are defined."""
        departments = [d.value for d in Department]
        assert len(departments) == 4
        assert "it_support" in departments
        assert "legal" in departments
        assert "credit_card" in departments
        assert "airport_ground" in departments

    def test_department_values_are_snake_case(self):
        """Verify department values follow snake_case convention."""
        for dept in Department:
            assert "_" in dept.value or dept.value == dept.value.lower()

    def test_department_enum_members(self):
        """Verify enum members are correctly named."""
        assert Department.IT_SUPPORT.value == "it_support"
        assert Department.LEGAL.value == "legal"
        assert Department.CREDIT_CARD.value == "credit_card"
        assert Department.AIRPORT_GROUND.value == "airport_ground"


class TestChatRequest:
    """Test ChatRequest validation and serialization."""

    def test_valid_request_minimal(self):
        """Verify minimal valid request (message only)."""
        req = ChatRequest(message="Hello, how do I reset my VPN?")
        assert req.message == "Hello, how do I reset my VPN?"
        assert req.department is None
        assert req.session_id is None

    def test_valid_request_with_all_fields(self):
        """Verify request with all fields."""
        req = ChatRequest(
            message="Credit card question",
            department=Department.CREDIT_CARD,
            session_id="sess_abc123",
        )
        assert req.message == "Credit card question"
        assert req.department == Department.CREDIT_CARD
        assert req.session_id == "sess_abc123"

    def test_missing_required_message_field(self):
        """Verify missing message raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest()
        assert "message" in str(exc_info.value)

    def test_message_must_be_string(self):
        """Verify message field rejects non-string types."""
        with pytest.raises(ValidationError):
            ChatRequest(message=123)

    def test_department_must_be_enum(self):
        """Verify department field accepts only Department enum values."""
        # Valid enum value
        req = ChatRequest(message="test", department=Department.IT_SUPPORT)
        assert req.department == Department.IT_SUPPORT

        # Invalid string (not enum value)
        with pytest.raises(ValidationError):
            ChatRequest(message="test", department="invalid_dept")

    def test_serialization_to_json(self):
        """Verify model_dump_json() produces valid JSON."""
        req = ChatRequest(
            message="test", department=Department.LEGAL, session_id="sess_123"
        )
        json_str = req.model_dump_json()
        assert isinstance(json_str, str)
        assert '"message":"test"' in json_str or '"message": "test"' in json_str
        assert "legal" in json_str
        assert "sess_123" in json_str

    def test_serialization_to_dict(self):
        """Verify model_dump() produces correct dictionary."""
        req = ChatRequest(
            message="test", department=Department.AIRPORT_GROUND, session_id="sess_xyz"
        )
        data = req.model_dump()
        assert data["message"] == "test"
        assert data["department"] == Department.AIRPORT_GROUND
        assert data["session_id"] == "sess_xyz"


class TestAgentTrace:
    """Test AgentTrace structure and validation."""

    def test_valid_agent_trace(self):
        """Verify valid AgentTrace with all required fields."""
        trace = AgentTrace(
            supervisor_decision="Route to IT_SUPPORT agent",
            agents_invoked=["it_support_agent"],
            retrieval_sources=[
                {"document": "vpn-setup.md", "score": 0.95},
                {"document": "troubleshooting.md", "score": 0.87},
            ],
            iterations=1,
        )
        assert trace.supervisor_decision == "Route to IT_SUPPORT agent"
        assert len(trace.agents_invoked) == 1
        assert len(trace.retrieval_sources) == 2
        assert trace.iterations == 1

    def test_agent_trace_multiple_agents(self):
        """Verify AgentTrace can have multiple agents invoked."""
        trace = AgentTrace(
            supervisor_decision="Cross-department query",
            agents_invoked=["it_support_agent", "legal_agent"],
            retrieval_sources=[],
            iterations=2,
        )
        assert len(trace.agents_invoked) == 2
        assert trace.iterations == 2

    def test_missing_required_fields(self):
        """Verify missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            AgentTrace(supervisor_decision="test")

        with pytest.raises(ValidationError):
            AgentTrace(agents_invoked=["agent"])


class TestChatResponse:
    """Test ChatResponse structure and validation."""

    def test_valid_response_minimal(self):
        """Verify valid response with required fields."""
        trace = AgentTrace(
            supervisor_decision="test",
            agents_invoked=["test_agent"],
            retrieval_sources=[],
            iterations=1,
        )
        resp = ChatResponse(
            answer="Your password can be reset via SSO.",
            department=Department.IT_SUPPORT,
            sources=["sso-guide.md"],
            confidence=0.92,
            trace=trace,
        )
        assert resp.answer == "Your password can be reset via SSO."
        assert resp.department == Department.IT_SUPPORT
        assert resp.confidence == 0.92

    def test_response_confidence_range(self):
        """Verify confidence is a valid float."""
        trace = AgentTrace(
            supervisor_decision="test",
            agents_invoked=["test_agent"],
            retrieval_sources=[],
            iterations=1,
        )
        # Valid confidence values
        resp = ChatResponse(
            answer="test",
            department=Department.LEGAL,
            sources=[],
            confidence=0.5,
            trace=trace,
        )
        assert resp.confidence == 0.5

    def test_response_sources_list(self):
        """Verify sources is a list of strings."""
        trace = AgentTrace(
            supervisor_decision="test",
            agents_invoked=["test_agent"],
            retrieval_sources=[],
            iterations=1,
        )
        resp = ChatResponse(
            answer="test",
            department=Department.CREDIT_CARD,
            sources=["doc1.md", "doc2.md", "doc3.md"],
            confidence=0.85,
            trace=trace,
        )
        assert len(resp.sources) == 3
        assert all(isinstance(s, str) for s in resp.sources)

    def test_response_serialization(self):
        """Verify ChatResponse serializes to JSON correctly."""
        trace = AgentTrace(
            supervisor_decision="test decision",
            agents_invoked=["agent1"],
            retrieval_sources=[{"doc": "test.md", "score": 0.9}],
            iterations=1,
        )
        resp = ChatResponse(
            answer="test answer",
            department=Department.AIRPORT_GROUND,
            sources=["test.md"],
            confidence=0.88,
            trace=trace,
        )
        json_str = resp.model_dump_json()
        assert isinstance(json_str, str)
        assert "test answer" in json_str


class TestChatStreamEvent:
    """Test ChatStreamEvent for streaming responses."""

    def test_valid_stream_token_event(self):
        """Verify valid token event."""
        event = ChatStreamEvent(type="token", data="Hello")
        assert event.type == "token"
        assert event.data == "Hello"

    def test_valid_stream_done_event(self):
        """Verify valid done event."""
        event = ChatStreamEvent(type="done", data=None)
        assert event.type == "done"
        assert event.data is None

    def test_stream_event_serialization(self):
        """Verify stream event serializes correctly."""
        event = ChatStreamEvent(type="token", data="streaming...")
        json_str = event.model_dump_json()
        assert "token" in json_str
        assert "streaming" in json_str


class TestDocumentChunk:
    """Test DocumentChunk validation and serialization."""

    def test_valid_chunk_minimal(self):
        """Verify minimal valid chunk."""
        chunk = DocumentChunk(id="chunk_001", content="VPN setup instructions go here.")
        assert chunk.id == "chunk_001"
        assert chunk.content == "VPN setup instructions go here."

    def test_valid_chunk_with_metadata(self):
        """Verify chunk with metadata."""
        metadata = DocumentMetadata(
            source="vpn-setup.md",
            department=Department.IT_SUPPORT,
            last_updated="2024-01-15",
        )
        chunk = DocumentChunk(
            id="chunk_002", content="Advanced VPN troubleshooting...", metadata=metadata
        )
        assert chunk.metadata.source == "vpn-setup.md"
        assert chunk.metadata.department == Department.IT_SUPPORT

    def test_missing_required_id(self):
        """Verify missing id raises ValidationError."""
        with pytest.raises(ValidationError):
            DocumentChunk(content="test")

    def test_missing_required_content(self):
        """Verify missing content raises ValidationError."""
        with pytest.raises(ValidationError):
            DocumentChunk(id="chunk_001")

    def test_chunk_serialization(self):
        """Verify chunk serializes to JSON."""
        chunk = DocumentChunk(id="chunk_003", content="Test content")
        json_str = chunk.model_dump_json()
        assert "chunk_003" in json_str
        assert "Test content" in json_str


class TestIngestionRequest:
    """Test IngestionRequest validation."""

    def test_valid_ingestion_request(self):
        """Verify valid ingestion request."""
        req = IngestionRequest(
            department=Department.LEGAL, file_path="data/legal/eu261-regulation.md"
        )
        assert req.department == Department.LEGAL
        assert req.file_path == "data/legal/eu261-regulation.md"

    def test_missing_required_fields(self):
        """Verify missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            IngestionRequest(department=Department.IT_SUPPORT)

        with pytest.raises(ValidationError):
            IngestionRequest(file_path="test.md")


class TestIngestionResult:
    """Test IngestionResult structure."""

    def test_valid_ingestion_result(self):
        """Verify valid ingestion result."""
        result = IngestionResult(
            department=Department.CREDIT_CARD,
            file_path="data/credit_card/rewards-policy.md",
            chunks_created=12,
            status="success",
        )
        assert result.department == Department.CREDIT_CARD
        assert result.chunks_created == 12
        assert result.status == "success"

    def test_ingestion_result_with_error(self):
        """Verify ingestion result can record errors."""
        result = IngestionResult(
            department=Department.AIRPORT_GROUND,
            file_path="missing.md",
            chunks_created=0,
            status="failed",
            error_message="File not found",
        )
        assert result.status == "failed"
        assert result.error_message == "File not found"


class TestRAGASMetrics:
    """Test RAGASMetrics structure."""

    def test_valid_ragas_metrics(self):
        """Verify valid RAGAS metrics."""
        metrics = RAGASMetrics(
            faithfulness=0.92,
            answer_relevancy=0.88,
            context_precision=0.95,
            context_recall=0.85,
        )
        assert metrics.faithfulness == 0.92
        assert metrics.answer_relevancy == 0.88

    def test_metrics_all_required(self):
        """Verify all metric fields are required."""
        with pytest.raises(ValidationError):
            RAGASMetrics(faithfulness=0.9)


class TestEvaluationRequest:
    """Test EvaluationRequest validation."""

    def test_valid_evaluation_request(self):
        """Verify valid evaluation request."""
        req = EvaluationRequest(conversation_id="conv_123")
        assert req.conversation_id == "conv_123"

    def test_missing_conversation_id(self):
        """Verify conversation_id is required."""
        with pytest.raises(ValidationError):
            EvaluationRequest()


class TestEvaluationResult:
    """Test EvaluationResult structure."""

    def test_valid_evaluation_result(self):
        """Verify valid evaluation result."""
        metrics = RAGASMetrics(
            faithfulness=0.90,
            answer_relevancy=0.87,
            context_precision=0.93,
            context_recall=0.82,
        )
        result = EvaluationResult(conversation_id="conv_456", metrics=metrics)
        assert result.conversation_id == "conv_456"
        assert result.metrics.faithfulness == 0.90

    def test_evaluation_result_with_timestamp(self):
        """Verify evaluation result includes timestamp."""
        metrics = RAGASMetrics(
            faithfulness=0.85,
            answer_relevancy=0.80,
            context_precision=0.90,
            context_recall=0.88,
        )
        result = EvaluationResult(conversation_id="conv_789", metrics=metrics)
        # Timestamp should be auto-generated
        assert result.evaluated_at is not None


class TestHealthResponse:
    """Test HealthResponse structure."""

    def test_valid_health_response(self):
        """Verify valid health response."""
        health = HealthResponse(status="healthy", version="1.0.0")
        assert health.status == "healthy"
        assert health.version == "1.0.0"

    def test_health_response_serialization(self):
        """Verify health response serializes correctly."""
        health = HealthResponse(status="ready", version="2.0.0")
        json_str = health.model_dump_json()
        assert (
            "healthy" in health.model_dump_json() or "ready" in health.model_dump_json()
        )


class TestErrorResponse:
    """Test ErrorResponse structure."""

    def test_valid_error_response(self):
        """Verify valid error response."""
        error = ErrorResponse(
            error="ValidationError", message="Invalid input provided", status_code=400
        )
        assert error.error == "ValidationError"
        assert error.message == "Invalid input provided"
        assert error.status_code == 400

    def test_error_response_with_details(self):
        """Verify error response can include additional details."""
        error = ErrorResponse(
            error="NotFoundError",
            message="Document not found",
            status_code=404,
            detail="Document ID: abc123",
        )
        assert error.detail == "Document ID: abc123"

    def test_error_response_serialization(self):
        """Verify error response serializes correctly."""
        error = ErrorResponse(
            error="ServerError", message="Internal server error", status_code=500
        )
        json_str = error.model_dump_json()
        assert "ServerError" in json_str
        assert "500" in json_str
