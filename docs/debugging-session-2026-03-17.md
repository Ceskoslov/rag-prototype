# 技术调试与系统修复总结 (2026-03-17)

## 1. 问题背景
在 SkyWing Airlines Multi-Agent RAG 系统的端到端测试过程中，发现了多个影响用户体验和系统稳定性的关键问题。主要现象包括前端页面崩溃（白屏）、后端流式响应格式异常以及整个聊天功能的不可用。

## 2. 诊断过程与根因分析

### 2.1 后端服务崩溃（根因）
**现象**：发送消息后，前端显示正在加载但随后停止，没有任何文字输出。后端日志抛出错误：`'_AsyncGeneratorContextManager' object has no attribute 'get_next_version'`。
**诊断**：错误源于 `SupervisorService` 的初始化过程。通过检查 `apps/backend/app/agents/supervisor.py`，发现系统尝试使用 `AsyncPostgresSaver.from_conn_string()` 作为 LangGraph 的 `checkpointer`。
**根因**：`AsyncPostgresSaver.from_conn_string()` 返回的是一个异步上下文管理器，它必须在 `async with` 块中使用。将其直接传递给 `workflow.compile(checkpointer=...)` 导致 LangGraph 在尝试调用持久化方法时失败。

### 2.2 前端 Agent Trace 面板白屏
**现象**：在某些请求成功返回 trace 数据后，前端侧边栏会导致整个页面白屏崩溃。浏览器控制台报错：`TypeError: Cannot read properties of undefined (reading 'map')`。
**诊断**：报错定位在 `AgentTracePanel.tsx`。当后端返回的 trace 数据中某些数组字段（如 `agents_invoked` 或 `retrieval_sources`）为 `null` 或 `undefined` 时，代码尝试直接调用 `.map()` 方法。
**根因**：前端组件缺乏对可选字段的空值保护。

### 2.3 SSE 流式响应连字问题
**现象**：流式输出的文本中，单词之间缺少空格，例如 "What is the procedure" 变成了 "Whatistheprocedure"。
**诊断**：检查 `apps/backend/app/services/chat.py` 中的 `chat_stream` 方法。
**根因**：代码在处理 `result.answer.split(" ")` 得到的 tokens 时，直接将其发送到前端，没有重新添加被 split 掉的空格。

## 3. 修复方案

### 3.1 修复后端持久化配置 (supervisor.py)
为了恢复系统功能，暂时将 `checkpointer` 替换为 `MemorySaver`，以避开异步上下文管理器的初始化复杂性。
```python
# apps/backend/app/agents/supervisor.py
from langgraph.checkpoint.memory import MemorySaver

def create_supervisor_graph(llm, department_agents):
    checkpointer = MemorySaver() # 替换 AsyncPostgresSaver
    # ...
    return workflow.compile(checkpointer=checkpointer)
```

### 3.2 增加前端健壮性 (AgentTracePanel.tsx)
在所有数组遍历操作前添加 `?? []` 空值保护，确保组件在数据缺失时不会崩溃。
```tsx
// apps/frontend/src/components/AgentTracePanel.tsx
{(trace.agents_invoked ?? []).map((agent) => (
  // ...
))}
```

### 3.3 修正流式 Token 拼接 (chat.py)
在发送 token 时，逻辑性地补充空格。
```python
# apps/backend/app/services/chat.py
tokens = [token for token in result.answer.split(" ") if token]
for i, token in enumerate(tokens):
    content = token if i == 0 else " " + token # 第一个 token 之后补空格
    yield self._sse({"type": "token", "content": content})
```

## 4. 验证结果

使用 Playwright 进行自动化回归测试，验证结果如下：
- **稳定性**：前端页面加载正常，多次发送消息未触发白屏。
- **功能性**：消息 "What is the procedure for setting up VPN access?" 能够正确触发 IT Support 智能体，并返回完整答案。
- **展示效果**：单词间空格显示正常；Agent Trace 面板正确显示 Iterations、Confidence 和检索来源（如 `vpn-setup.md`）。
- **路由逻辑**：系统能正确识别意图（如 baggage 咨询路由至 Airport Ground，VPN 咨询路由至 IT Support）。

## 5. 当前状态与后续建议

### 当前状态
- ✅ 端到端聊天流完全恢复正常。
- ✅ 前端交互体验大幅提升，不再崩溃且排版正确。

### 已知小问题
- **Routing Decision 显示 "unknown"**：当用户显式选择部门（Explicit Routing）时，系统绕过了 supervisor 的自动路由决策提取逻辑。这属于 UI 显示层面的优化项，不影响核心业务逻辑。

### 后续建议
1. **持久化升级**：后续需重新实现 `AsyncPostgresSaver` 的正确异步初始化逻辑，以支持生产环境下的多轮对话持久化。
2. **UI 增强**：针对显式路由场景，优化 `AgentTracePanel` 的显示逻辑，避免出现 "unknown" 字样。
