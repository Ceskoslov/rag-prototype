from __future__ import annotations

import importlib
from typing import Any

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage

from app.schemas.common import Department

supervisor_module = importlib.import_module("app.agents.supervisor")
SUPERVISOR_SYSTEM_PROMPT = supervisor_module.SUPERVISOR_SYSTEM_PROMPT
SupervisorResult = supervisor_module.SupervisorResult
SupervisorService = supervisor_module.SupervisorService
create_supervisor_graph = supervisor_module.create_supervisor_graph


class FakeAgent:
    def __init__(
        self,
        response: str | None = None,
        *,
        timeout: bool = False,
        name: str = "fake_agent",
    ) -> None:
        self.response = response or "ok"
        self.timeout = timeout
        self.name = name
        self.calls: list[dict[str, Any]] = []

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(state)
        if self.timeout:
            raise TimeoutError("agent timed out")
        return {"messages": [AIMessage(content=self.response, name="department_agent")]}


class FakeSupervisorGraph:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(state)
        return self.result


def _all_departments() -> dict[Department, FakeAgent]:
    return {
        Department.IT_SUPPORT: FakeAgent("IT support guidance"),
        Department.LEGAL: FakeAgent("Legal guidance"),
        Department.CREDIT_CARD: FakeAgent("Credit card guidance"),
        Department.AIRPORT_GROUND: FakeAgent("Airport guidance"),
    }


def test_create_supervisor_graph_uses_expected_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeWorkflow:
        def compile(self, checkpointer: Any = None) -> str:
            return "compiled-graph"

    def fake_create_supervisor(**kwargs: Any) -> FakeWorkflow:
        captured.update(kwargs)
        return FakeWorkflow()

    monkeypatch.setattr(supervisor_module, "create_supervisor", fake_create_supervisor)

    model = FakeListChatModel(responses=["route"])
    graph = create_supervisor_graph(model, _all_departments())

    assert graph == "compiled-graph"
    assert captured["model"] is model
    assert captured["output_mode"] == "full_history"
    assert captured["prompt"] == SUPERVISOR_SYSTEM_PROMPT
    assert len(captured["agents"]) == 4


def test_single_department_routing_uses_it_support(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    supervisor_result = {
        "messages": [AIMessage(content="Please reset VPN via IT playbook.")],
        "routing_decision": {
            "departments": [Department.IT_SUPPORT.value],
            "confidence": 0.87,
        },
    }
    fake_graph = FakeSupervisorGraph(supervisor_result)
    monkeypatch.setattr(
        supervisor_module,
        "create_supervisor_graph",
        lambda llm, agents: fake_graph,
    )
    service = SupervisorService(FakeListChatModel(responses=["it"]), _all_departments())

    result = service.route_query("How do I reset VPN?")

    assert isinstance(result, SupervisorResult)
    assert result.departments_used == [Department.IT_SUPPORT]
    assert "VPN" in result.answer
    assert result.confidence == 0.87


def test_multi_department_routing_uses_airport_and_credit_card(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    supervisor_result = {
        "messages": [
            AIMessage(content="Airport confirmed delay; card team started refund."),
        ],
        "routing_decision": {
            "departments": [
                Department.AIRPORT_GROUND.value,
                Department.CREDIT_CARD.value,
            ],
            "confidence": 0.79,
        },
    }
    fake_graph = FakeSupervisorGraph(supervisor_result)
    monkeypatch.setattr(
        supervisor_module,
        "create_supervisor_graph",
        lambda llm, agents: fake_graph,
    )
    service = SupervisorService(
        FakeListChatModel(responses=["multi"]), _all_departments()
    )

    result = service.route_query(
        "My flight was delayed and I need a credit card refund"
    )

    assert set(result.departments_used) == {
        Department.AIRPORT_GROUND,
        Department.CREDIT_CARD,
    }
    assert len(result.departments_used) == 2
    assert "refund" in result.answer.lower()


def test_explicit_department_skips_supervisor_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    departments = _all_departments()
    explicit_graph = FakeSupervisorGraph(
        {"messages": [AIMessage(content="should not run")]}
    )
    monkeypatch.setattr(
        supervisor_module,
        "create_supervisor_graph",
        lambda llm, agents: explicit_graph,
    )
    service = SupervisorService(FakeListChatModel(responses=["route"]), departments)

    result = service.route_query(
        "Need help with email login", department=Department.IT_SUPPORT
    )

    assert explicit_graph.calls == []
    assert result.departments_used == [Department.IT_SUPPORT]
    assert result.confidence == 0.9
    assert "guidance" in result.answer.lower()


def test_parse_supervisor_structured_output_with_routing_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        supervisor_module,
        "create_supervisor_graph",
        lambda llm, agents: FakeSupervisorGraph({"messages": []}),
    )
    service = SupervisorService(
        FakeListChatModel(responses=["route"]), _all_departments()
    )
    raw_result = {
        "messages": [AIMessage(content="Escalated to legal for compliance review")],
        "routing_decision": {
            "departments": [Department.LEGAL],
            "confidence": 0.66,
        },
    }

    parsed = service._parse_supervisor_result(raw_result)

    assert parsed.departments_used == [Department.LEGAL]
    assert parsed.confidence == 0.66
    assert len(parsed.agent_traces) == 1


def test_graceful_timeout_handling_for_explicit_department(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    departments = _all_departments()
    departments[Department.IT_SUPPORT] = FakeAgent(timeout=True)
    monkeypatch.setattr(
        supervisor_module,
        "create_supervisor_graph",
        lambda llm, agents: FakeSupervisorGraph({"messages": []}),
    )
    service = SupervisorService(FakeListChatModel(responses=["route"]), departments)

    result = service.route_query("VPN broke", department=Department.IT_SUPPORT)

    assert result.departments_used == [Department.IT_SUPPORT]
    assert "timed out" in result.answer.lower()
    assert result.confidence == 0.0
