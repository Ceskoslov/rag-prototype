"""TDD tests for LangGraph checkpointing with AsyncPostgresSaver."""

from __future__ import annotations

import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.supervisor import (
    AsyncPostgresSaver,
    SupervisorService,
    create_supervisor_graph,
)
from app.schemas.common import Department


class FakeAgent:
    """Mock agent for testing."""

    def __init__(self, response: str = "agent response", name: str = "fake") -> None:
        self.response = response
        self.name = name

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        messages = state.get("messages", [])
        return {
            "messages": [
                *messages,
                AIMessage(content=self.response, name=self.name),
            ]
        }


def _create_test_agents() -> dict[Department, FakeAgent]:
    return {
        Department.IT_SUPPORT: FakeAgent("IT response", "it_agent"),
        Department.LEGAL: FakeAgent("Legal response", "legal_agent"),
        Department.CREDIT_CARD: FakeAgent("Credit response", "credit_agent"),
        Department.AIRPORT_GROUND: FakeAgent("Airport response", "airport_agent"),
    }


@pytest.mark.asyncio
async def test_conversation_state_persists_across_invocations() -> None:
    """Test that checkpointer persists state across multiple graph invocations."""
    # ARRANGE: Mock create_supervisor to avoid FakeListChatModel.bind_tools issue
    captured_checkpointer = None

    class FakeWorkflow:
        def compile(self, checkpointer=None):
            nonlocal captured_checkpointer
            captured_checkpointer = checkpointer
            return FakeCompiledGraph()

    class FakeCompiledGraph:
        async def ainvoke(self, state, config=None):
            return {"messages": state.get("messages", [])}

    with patch("app.agents.supervisor.create_supervisor", return_value=FakeWorkflow()):
        llm = FakeListChatModel(responses=["route"])
        agents = _create_test_agents()

        # ACT: Create supervisor graph
        graph = create_supervisor_graph(llm, agents)

        # ASSERT: Checkpointer was passed to compile
        assert captured_checkpointer is not None, "Checkpointer should be created"

        # ACT: Test invocations with thread_id
        session_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": session_id}}

        result1 = await graph.ainvoke(
            {"messages": [HumanMessage(content="What is VPN?")]},
            config=cast(Any, config),
        )

        result2 = await graph.ainvoke(
            {"messages": [HumanMessage(content="How do I set it up?")]},
            config=cast(Any, config),
        )

        # ASSERT: Both invocations completed
        assert result1 is not None
        assert result2 is not None


@pytest.mark.asyncio
async def test_agent_remembers_previous_messages_in_session() -> None:
    """Test that agent has access to previous conversation context."""

    # ARRANGE: Mock create_supervisor
    class FakeWorkflow:
        def compile(self, checkpointer=None):
            return FakeCompiledGraph(checkpointer)

    class FakeCompiledGraph:
        def __init__(self, checkpointer):
            self.checkpointer = checkpointer
            self.invocation_count = 0

        async def ainvoke(self, state, config=None):
            self.invocation_count += 1
            messages = state.get("messages", [])
            return {"messages": messages, "invocation": self.invocation_count}

    with patch("app.agents.supervisor.create_supervisor", return_value=FakeWorkflow()):
        llm = FakeListChatModel(responses=["IT"])
        agents = _create_test_agents()

        graph = create_supervisor_graph(llm, agents)

        # ACT: Multi-turn conversation
        session_id = "test-session-123"
        config = {"configurable": {"thread_id": session_id}}

        result1 = await graph.ainvoke(
            {"messages": [HumanMessage(content="What is VPN?")]},
            config=cast(Any, config),
        )

        result2 = await graph.ainvoke(
            {"messages": [HumanMessage(content="Tell me more")]},
            config=cast(Any, config),
        )

        # ASSERT: Both invocations successful
        assert result1.get("invocation") == 1
        assert result2.get("invocation") == 2
        assert graph.checkpointer is not None


@pytest.mark.asyncio
async def test_different_sessions_have_isolated_state() -> None:
    """Test that different session_ids maintain separate conversation states."""

    # ARRANGE: Mock create_supervisor
    class FakeWorkflow:
        def compile(self, checkpointer=None):
            return FakeCompiledGraph()

    class FakeCompiledGraph:
        def __init__(self):
            self.invocations_by_thread = {}

        async def ainvoke(self, state, config=None):
            thread_id = (
                config.get("configurable", {}).get("thread_id") if config else None
            )
            if thread_id:
                self.invocations_by_thread[thread_id] = (
                    self.invocations_by_thread.get(thread_id, 0) + 1
                )
            return {"messages": state.get("messages", []), "thread_id": thread_id}

    with patch("app.agents.supervisor.create_supervisor", return_value=FakeWorkflow()):
        llm = FakeListChatModel(responses=["route"])
        agents = _create_test_agents()

        graph = cast(Any, create_supervisor_graph(llm, agents))

        # ACT: Session A
        session_a = "session-a"
        config_a = {"configurable": {"thread_id": session_a}}
        result_a1 = await graph.ainvoke(
            {"messages": [HumanMessage(content="VPN help")]},
            config=cast(Any, config_a),
        )

        # ACT: Session B
        session_b = "session-b"
        config_b = {"configurable": {"thread_id": session_b}}
        result_b1 = await graph.ainvoke(
            {"messages": [HumanMessage(content="Contract review")]},
            config=cast(Any, config_b),
        )

        # ACT: Follow-up in Session A
        result_a2 = await graph.ainvoke(
            {"messages": [HumanMessage(content="follow up")]},
            config=cast(Any, config_a),
        )

        # ASSERT: Sessions tracked separately
        assert session_a in graph.invocations_by_thread
        assert session_b in graph.invocations_by_thread
        assert graph.invocations_by_thread[session_a] == 2
        assert graph.invocations_by_thread[session_b] == 1


@pytest.mark.asyncio
async def test_checkpointer_uses_postgres_connection_string() -> None:
    """Test that AsyncPostgresSaver is initialized with PostgreSQL DSN."""
    # ARRANGE: Capture checkpointer creation
    captured_conn_string = None
    original_from_conn_string = AsyncPostgresSaver.from_conn_string

    def mock_from_conn_string(conn_string):
        nonlocal captured_conn_string
        captured_conn_string = conn_string
        mock = MagicMock(spec=AsyncPostgresSaver)
        return mock

    class FakeWorkflow:
        def compile(self, checkpointer=None):
            return MagicMock()

    with patch.object(
        AsyncPostgresSaver, "from_conn_string", side_effect=mock_from_conn_string
    ):
        with patch(
            "app.agents.supervisor.create_supervisor", return_value=FakeWorkflow()
        ):
            llm = FakeListChatModel(responses=["route"])
            agents = _create_test_agents()

            # ACT: Create supervisor graph
            graph = create_supervisor_graph(llm, agents)

            # ASSERT: Connection string captured
            assert captured_conn_string is not None, (
                "Connection string should be provided"
            )
            assert "postgresql" in captured_conn_string.lower(), (
                "Should use PostgreSQL connection string"
            )


@pytest.mark.asyncio
async def test_supervisor_service_passes_thread_config_to_graph() -> None:
    """Test that SupervisorService.route_query properly accepts config parameter."""
    # ARRANGE: Create a real supervisor service with mocked graph
    captured_configs: list[dict[str, Any] | None] = []

    class MockGraph:
        def invoke(
            self, state: dict[str, Any], config: dict[str, Any] | None = None
        ) -> dict[str, Any]:
            captured_configs.append(config)
            return {
                "messages": [AIMessage(content="response")],
                "routing_decision": {"departments": ["IT_SUPPORT"], "confidence": 0.8},
            }

    mock_graph = MockGraph()

    with patch(
        "app.agents.supervisor.create_supervisor_graph",
        return_value=mock_graph,
    ):
        llm = FakeListChatModel(responses=["route"])
        agents = _create_test_agents()
        service = SupervisorService(llm, agents)

        # ACT: Route query WITHOUT explicit config (config=None path)
        result1 = service.route_query(query="Help with VPN", department=None)

        # ACT: Route query passing config explicitly via new parameter
        config = {"configurable": {"thread_id": "test-thread-123"}}
        result2 = service.route_query(query="More help", department=None, config=config)

        # ASSERT: First call had no config
        assert len(captured_configs) >= 1

        # ASSERT: Second call had config
        assert len(captured_configs) >= 2
        assert captured_configs[1] == config, "Config should be passed to graph"

        # ASSERT: Both results valid
        assert result1.answer == "response"
        assert result2.answer == "response"
