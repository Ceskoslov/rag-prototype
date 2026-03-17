from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypedDict, cast

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent

from app.agents.self_rag import create_self_rag_graph
from app.core.logging import get_logger
from app.schemas.common import Department

logger = get_logger(__name__)
DEFAULT_AGENT_TIMEOUT_SECONDS = 30.0


class RetrieverLike(Protocol):
    def invoke(
        self,
        query: str,
        config: Mapping[str, Any] | None = None,
    ) -> list[Any]: ...


class AgentLike(Protocol):
    async def ainvoke(self, state: Mapping[str, Any]) -> Mapping[str, Any]: ...


class SelfRAGResult(TypedDict, total=False):
    generation: str
    confidence: float


@dataclass(frozen=True)
class DepartmentAgentConfig:
    department: Department
    prompt: str
    name: str


SYSTEM_PROMPTS: dict[Department, str] = {
    Department.IT_SUPPORT: (
        "You are an IT Support specialist for SkyWing Airlines. "
        "Help employees with technical issues, VPN, email, software, hardware. "
        "Use the rag_search tool to find solutions from the knowledge base."
    ),
    Department.LEGAL: (
        "You are a Legal advisor for SkyWing Airlines. "
        "Provide guidance on contracts, compliance, employment law, regulations. "
        "Use the rag_search tool to reference legal documents."
    ),
    Department.CREDIT_CARD: (
        "You are a Credit Card support specialist for SkyWing Airlines rewards program. "
        "Assist customers with points, redemption, benefits, billing issues. "
        "Use the rag_search tool to find program details."
    ),
    Department.AIRPORT_GROUND: (
        "You are an Airport Ground Services coordinator for SkyWing Airlines. "
        "Help with baggage handling, flight operations, gate procedures, equipment. "
        "Use the rag_search tool to find operational procedures."
    ),
}


def _build_department_config(department: Department) -> DepartmentAgentConfig:
    prompt = SYSTEM_PROMPTS[department]
    return DepartmentAgentConfig(
        department=department,
        prompt=prompt,
        name=f"{department.value}_agent",
    )


def _extract_generation(result: Mapping[str, Any]) -> str:
    generation = result.get("generation")
    if generation is None:
        return "No answer available."
    return str(generation)


def _extract_source_metadata(result: Mapping[str, Any]) -> list[dict[str, str]]:
    docs = result.get("documents")
    if not isinstance(docs, list):
        return []
    sources: list[dict[str, str]] = []
    seen_titles: set[str] = set()
    for doc in docs:
        if not isinstance(doc, Document):
            continue
        metadata = doc.metadata or {}
        title = str(metadata.get("source_file", metadata.get("title", "unknown")))
        if title in seen_titles:
            continue
        seen_titles.add(title)
        snippet = doc.page_content[:200] if doc.page_content else ""
        sources.append(
            {
                "title": title,
                "snippet": snippet,
                "department": str(metadata.get("department", "")),
            }
        )
    return sources


def create_department_agent(
    department: Department,
    llm: BaseChatModel,
    retriever: RetrieverLike | Any,
) -> CompiledGraph:
    config = _build_department_config(department)
    self_rag_graph = create_self_rag_graph(llm=llm, retriever=retriever)

    @tool
    def rag_search(query: str) -> str:
        """Search department knowledge base using Self-RAG."""
        logger.info(
            "department_rag_search", department=config.department.value, query=query
        )
        result = cast(
            SelfRAGResult,
            self_rag_graph.invoke(
                {
                    "query": query,
                    "department": config.department.value,
                }
            ),
        )
        generation = _extract_generation(result)
        sources = _extract_source_metadata(result)
        return json.dumps(
            {"answer": generation, "sources": sources},
            ensure_ascii=False,
        )

    return create_react_agent(
        model=llm,
        tools=[rag_search],
        name=config.name,
        prompt=config.prompt,
    )


def create_all_agents(
    llm: BaseChatModel,
    retriever: RetrieverLike | Any,
) -> dict[Department, CompiledGraph]:
    return {
        department: create_department_agent(
            department=department,
            llm=llm,
            retriever=retriever,
        )
        for department in Department
    }


class DepartmentAgentFactory:
    llm: BaseChatModel
    retriever: RetrieverLike | Any

    def __init__(
        self,
        llm: BaseChatModel,
        retriever: RetrieverLike | Any,
    ) -> None:
        self.llm = llm
        self.retriever = retriever

    def create(self, department: Department) -> CompiledGraph:
        return create_department_agent(
            department=department,
            llm=self.llm,
            retriever=self.retriever,
        )

    def create_all(self) -> dict[Department, CompiledGraph]:
        return create_all_agents(llm=self.llm, retriever=self.retriever)


async def invoke_agent_with_timeout(
    agent: AgentLike | Any,
    state: Mapping[str, Any],
    timeout: float = DEFAULT_AGENT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    try:
        result = await asyncio.wait_for(agent.ainvoke(state), timeout=timeout)
    except asyncio.TimeoutError:
        return {"error": "Agent timed out after 30 seconds"}
    return dict(result)
