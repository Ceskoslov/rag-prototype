from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph_supervisor import create_supervisor

from app.agents.department import create_all_agents
from app.schemas.common import Department

SUPERVISOR_SYSTEM_PROMPT = """
You are a routing supervisor for SkyWing Airlines multi-agent system.

Your role:
- Analyze the user's query to determine which department(s) can help
- Route to a SINGLE agent for clear single-department queries
- Route to MULTIPLE agents for cross-department queries
- Synthesize multi-agent responses into a coherent answer

Available departments:
- IT Support: Technical issues, VPN, email, software, hardware
- Legal: Contracts, compliance, employment law, regulations
- Credit Card: Rewards program, points, redemption, benefits, billing
- Airport Ground Services: Baggage, flight operations, gate procedures, equipment

When in doubt, route to the most relevant single department.
""".strip()


class AgentLike(Protocol):
    def invoke(self, state: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class SupervisorResult:
    answer: str
    departments_used: list[Department]
    agent_traces: list[dict[str, Any]]
    confidence: float


def create_supervisor_graph(
    llm: BaseChatModel,
    department_agents: Mapping[Department, CompiledStateGraph],
) -> CompiledGraph:
    workflow = create_supervisor(
        agents=cast(list[CompiledStateGraph], list(department_agents.values())),
        model=llm,
        prompt=SUPERVISOR_SYSTEM_PROMPT,
        output_mode="full_history",
    )
    return workflow.compile()


class SupervisorService:
    def __init__(
        self,
        llm: BaseChatModel,
        department_agents: Mapping[Department, CompiledGraph | AgentLike],
    ) -> None:
        self.supervisor_graph = create_supervisor_graph(
            llm,
            cast(Mapping[Department, CompiledStateGraph], department_agents),
        )
        self.department_agents: dict[Department, CompiledGraph | AgentLike] = dict(
            department_agents
        )

    def route_query(
        self,
        query: str,
        department: Department | None = None,
    ) -> SupervisorResult:
        if department is not None:
            return self._route_explicit_department(query, department)

        result = self.supervisor_graph.invoke({"messages": [("user", query)]})
        return self._parse_supervisor_result(result)

    def _route_explicit_department(
        self,
        query: str,
        department: Department,
    ) -> SupervisorResult:
        if department not in self.department_agents:
            raise ValueError(f"Unknown department: {department}")

        agent = self.department_agents[department]
        try:
            result = agent.invoke({"messages": [("user", query)]})
        except TimeoutError:
            return SupervisorResult(
                answer="Department agent timed out while processing the request.",
                departments_used=[department],
                agent_traces=[{"error": "timeout", "department": department.value}],
                confidence=0.0,
            )

        messages = result.get("messages", [])
        answer = (
            self._message_text(messages[-1]) if messages else "No answer available."
        )
        return SupervisorResult(
            answer=answer,
            departments_used=[department],
            agent_traces=[result],
            confidence=0.9,
        )

    def _parse_supervisor_result(self, result: dict[str, Any]) -> SupervisorResult:
        messages = result.get("messages", [])
        answer = (
            self._message_text(messages[-1]) if messages else "No answer available."
        )

        departments_used = self._extract_departments(result)
        confidence = self._extract_confidence(result, len(departments_used))

        return SupervisorResult(
            answer=answer,
            departments_used=departments_used,
            agent_traces=[result],
            confidence=confidence,
        )

    def _extract_departments(self, result: dict[str, Any]) -> list[Department]:
        decision = result.get("routing_decision", {})
        raw_departments = decision.get("departments", [])

        parsed: list[Department] = []
        for raw in raw_departments:
            department = self._to_department(raw)
            if department is not None and department not in parsed:
                parsed.append(department)

        return parsed

    def _extract_confidence(self, result: dict[str, Any], count: int) -> float:
        decision = result.get("routing_decision", {})
        raw_confidence = decision.get("confidence")
        if isinstance(raw_confidence, (int, float)):
            return max(0.0, min(1.0, float(raw_confidence)))
        if count > 1:
            return 0.72
        if count == 1:
            return 0.78
        return 0.5

    def _to_department(self, raw: Any) -> Department | None:
        if isinstance(raw, Department):
            return raw
        if not isinstance(raw, str):
            return None
        normalized = raw.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "it_support": Department.IT_SUPPORT,
            "legal": Department.LEGAL,
            "credit_card": Department.CREDIT_CARD,
            "airport_ground": Department.AIRPORT_GROUND,
            "airport_ground_services": Department.AIRPORT_GROUND,
        }
        return aliases.get(normalized)

    def _message_text(self, message: Any) -> str:
        if isinstance(message, BaseMessage):
            return str(message.content)
        if isinstance(message, tuple) and len(message) >= 2:
            return str(message[1])
        return str(message)


def create_supervisor_service(llm: BaseChatModel, retriever: Any) -> SupervisorService:
    department_agents = create_all_agents(llm, retriever)
    return SupervisorService(llm=llm, department_agents=department_agents)
