from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import Any, override

import pytest
from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph.graph import CompiledGraph

from app.agents.department import (
    SYSTEM_PROMPTS,
    create_all_agents,
    create_department_agent,
    invoke_agent_with_timeout,
)
from app.schemas.common import Department


class ToolCallingFakeListChatModel(FakeListChatModel):
    bound_tools: list[str] = []

    @override
    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable[..., Any] | BaseTool],
        **kwargs: Any,
    ) -> ToolCallingFakeListChatModel:
        _ = kwargs
        self.bound_tools = [getattr(tool, "name", "") for tool in tools]
        return self

    def _next_response(self) -> str:
        response = self.responses[self.i]
        if self.i < len(self.responses) - 1:
            self.i += 1
        else:
            self.i = 0
        return response

    @override
    def invoke(
        self,
        input: Any,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AIMessage:
        _ = config, kwargs
        if isinstance(input, str):
            if input.startswith("Evaluate the answer quality"):
                return AIMessage(content="approved\nconfidence: 0.92")
            if input.startswith("Rewrite the query"):
                return AIMessage(content="refined query")
            return AIMessage(content="Generated answer from retrieved context.")

        response = self._next_response()

        if response.startswith("TOOL:"):
            _, tool_name, tool_input = response.split(":", 2)
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": f"call_{self.i}",
                        "name": tool_name,
                        "args": {"query": tool_input},
                    }
                ],
            )
        return AIMessage(content=response)

    @override
    async def ainvoke(
        self,
        input: Any,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AIMessage:
        return self.invoke(input=input, config=config, **kwargs)


class RecordingRetriever:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def invoke(
        self,
        query: str,
        config: dict[str, Any] | None = None,
    ) -> list[Document]:
        metadata = config or {}
        department = str(metadata.get("department", "unknown"))
        self.calls.append({"query": query, "config": metadata})
        return [
            Document(
                page_content=f"{department} knowledge result for: {query}",
                metadata={"department": department},
            )
        ]


def test_create_department_agent_returns_compiled_react_graph() -> None:
    llm = ToolCallingFakeListChatModel(responses=["Final answer"])
    retriever = RecordingRetriever()

    agent = create_department_agent(Department.IT_SUPPORT, llm, retriever)

    assert isinstance(agent, CompiledGraph)
    assert agent.name == "it_support_agent"


def test_each_agent_uses_department_scoped_rag_search_tool() -> None:
    retriever = RecordingRetriever()
    it_agent = create_department_agent(
        Department.IT_SUPPORT,
        ToolCallingFakeListChatModel(responses=["TOOL:rag_search:vpn", "done"]),
        retriever,
    )
    legal_agent = create_department_agent(
        Department.LEGAL,
        ToolCallingFakeListChatModel(responses=["TOOL:rag_search:contract", "done"]),
        retriever,
    )

    it_agent.invoke({"messages": [("user", "Help with VPN")]})
    legal_agent.invoke({"messages": [("user", "Need contract guidance")]})

    departments = [call["config"]["department"] for call in retriever.calls]
    assert departments == [Department.IT_SUPPORT.value, Department.LEGAL.value]


def test_agent_invocation_returns_messages_with_tool_call_results() -> None:
    llm = ToolCallingFakeListChatModel(
        responses=[
            "TOOL:rag_search:vpn reset",
            "Use the documented VPN reset procedure.",
        ]
    )
    retriever = RecordingRetriever()
    agent = create_department_agent(Department.IT_SUPPORT, llm, retriever)

    result = agent.invoke({"messages": [("user", "How do I reset VPN?")]})
    message_types = [message.type for message in result["messages"]]

    assert "tool" in message_types
    assert result["messages"][-1].content == "Use the documented VPN reset procedure."
    assert len(str(result["messages"][-2].content)) > 0


@pytest.mark.asyncio
async def test_invoke_agent_with_timeout_enforces_limit() -> None:
    class SlowAgent:
        async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
            _ = state
            await asyncio.sleep(0.05)
            return {"ok": True}

    result = await invoke_agent_with_timeout(
        SlowAgent(), {"messages": []}, timeout=0.001
    )

    assert result == {"error": "Agent timed out after 30 seconds"}


def test_create_all_agents_creates_four_agents_with_unique_prompts() -> None:
    llm = ToolCallingFakeListChatModel(responses=["Final answer"])
    retriever = RecordingRetriever()

    agents = create_all_agents(llm, retriever)

    assert set(agents.keys()) == set(Department)
    assert all(isinstance(agent, CompiledGraph) for agent in agents.values())
    assert len(set(SYSTEM_PROMPTS.values())) == 4
