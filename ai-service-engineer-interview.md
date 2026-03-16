# Draft: AI Service Engineer 面试准备

## Requirements (confirmed)
- **职位**: AI Service Engineer
- **时间线**: 1 周左右 — 需要系统但有优先级的准备
- **当前水平**: AutoGen/Semantic Kernel 熟练, LangChain 初学
- **面试环节**: 技术面（编程/系统设计）+ 项目深挖面 + 行为面（STAR）
- **简历项目核心**: RAG + 多智能体混合系统（Microsoft Agent Framework: AutoGen + Semantic Kernel）
- **前端**: React + TypeScript
- **后端**: Python + FastAPI
- **目标职位技术栈**: LangChain, Claude Agent SDK, MCP, RFT, Memory Engineering, Skill标准化

## Key Challenge
- 需要将 AutoGen/SK 经验**映射**到 LangChain/Claude SDK 生态
- RFT 是弱项，需要补充
- MCP、Skill标准化是新兴概念，需要快速掌握
- 项目包装需要突出**可迁移能力**，而非框架锁定

## Technical Decisions
- 准备方向: 全面覆盖（技术知识 + 项目包装 + 面试题库）
- 优先级: LangChain快速上手 > 项目包装策略 > 新概念补充(RFT/MCP) > 行为面准备

## Project Details (confirmed)
- **项目性质**: 面向企业内部员工的知识库系统，月均1万用户
- **项目最大技术挑战**: RAG 检索质量/准确率优化
- **多智能体编排模式**: Supervisor 模式
- **项目成熟度**: 生产级产品，已在持续使用中

## JD 关键要求分析 [COMPLETED]

### 职位描述核心关键词
1. **端到端自动化链路Agent** — 业务场景驱动，工作流集成
2. **Agentic Loop** — 任务拆解, Planning, Reflection, 动态工具调用
3. **Memory Extraction + 长效记忆** — 长文本/录音上下文，动态注入+压缩
4. **MCP标准化 + Skill生态** — 插件/工具集编排，Sub-agents集成
5. **RFT + LLM-as-a-judge** — 在线评测，Bad Case优化

### 岗位要求匹配度分析
| 要求 | 你的现状 | Gap | 准备策略 |
|------|----------|-----|----------|
| ✅ 2年+ LLM产品开发 | 有生产级RAG+多Agent项目 | 无 | 强化项目包装 |
| ✅ Plan/ReAct/Context/Memory理解 | AutoGen/SK有实践 | **需映射到通用概念** | 知识体系建立 |
| ⚠️ 完整Agent项目落地 | 有，但用AutoGen/SK | **需翻译到LangChain语境** | 框架映射+术语对齐 |
| ⚠️ 精通自主编排 | Supervisor模式有实践 | **DeepAgents不熟** | 快速补课+找相似性 |
| ❌ Multi-agent协作/Loop/状态管理 | 有经验但需具体化 | **需准备深挖故事** | 技术挑战案例准备 |
| ✅ 长文本/多轮对话信息抽取 | RAG优化经验直接相关 | 无 | 这是你的强项，重点包装 |
| ⚠️ MCP协议 | 调研已完成 | **理论→实践gap** | 背熟核心概念+示例 |
| ✅ RAG实践 | 生产级经验 | 无 | 混合搜索优化是亮点 |
| ❌ RFT经验 | 无 | **知识空白** | 理论补充，诚实但show学习能力 |

### 加分项机会点
| 加分项 | 现状 | 策略 |
|--------|------|------|
| Claude Agent SDK/langchain-deepagents | 不熟 | **调研补充，show快速学习** |
| Vibe Coding | 未知你的能力 | **面试时展示AI辅助开发思维** |
| Deep Research Agent | 无直接经验 | **将RAG系统包装为研究员原型** |

### 高频面试问题预测（基于JD）
1. **"设计一个端到端的录音转知识的自动化链路"** (核心场景)
2. **"你的Agent如何做Planning和Reflection?"** (Agentic Loop)
3. **"如何处理超长会话的Memory管理?"** (长效记忆)
4. **"解释你对MCP的理解，如何设计Skill标准化?"** (协议标准)
5. **"如何评估Agent质量并优化Bad Case?"** (RFT/评测体系)

## Scope Boundaries
- INCLUDE: 技术知识体系、项目包装策略、面试题库+答案、行为面STAR模板
- EXCLUDE: 实际编码练习（这是准备计划，不是coding bootcamp）

## Research Findings (Completed)

### 调研1: LangChain 核心架构 [DONE]
- LCEL = Runnable 协议 (invoke/batch/stream/ainvoke/abatch/astream)
- LangGraph = 状态机 (StateGraph, Nodes, Edges, Conditional Edges, Checkpointing)
- LangSmith = 可观测性平台 (Tracing, Monitoring, Evaluation)
- 高级RAG: 混合搜索(BM25+Vector+RRF), 交叉编码器重排序, 多查询检索, 父文档检索
- RAG评估: Faithfulness, Relevance, Groundedness, Context Precision/Recall
- Agent: ReAct → 工具调用Agent(原生function calling), 多Agent(Supervisor/Hierarchical/Peer)
- 生产模式: 流式输出(values/updates/messages), 异步+批处理, 错误处理+降级, 速率限制

### 调研2: Claude SDK + AutoGen/SK + RFT + Memory [DONE]
- Claude: tool_use API, Extended Thinking, Prompt Caching(90%成本降低), Advanced Tool Use
- AutoGen vs SK: AutoGen=多Agent对话框架, SK=AI中间件/插件系统
- Microsoft Agent Framework (2026 RC): 统一AutoGen+SK, 支持MCP/A2A
- RFT: SFT→PPO→DPO→GRPO (GRPO=最新, <100样本, 无需奖励模型)
- MCP: Client-Server模型, Tools/Resources/Prompts三原语, JSON-RPC协议
- Skill标准化: SKILL.md标准, 20-50%性能提升, Tools<Plugins<Skills
- Memory: 向量存储 vs 图存储 vs 混合, Mem0/Zep/Letta框架

### 调研3: 端到端自动化 + 面试策略 [DONE]
- 端到端链路: Sequential/Parallel/Conditional分支, 重试/降级/死信队列
- 多Agent编排对比: LangGraph(精确控制) vs AutoGen(对话驱动) vs CrewAI(角色团队)
- 生产架构: FastAPI(SSE/WebSocket), JWT+限流+成本追踪, Celery后台处理
- 项目包装: C.A.R.框架(Context-Architecture-Results), 准备3-4个深挖故事
- 框架映射: AutoGen概念→LangChain等价物表, 可迁移模式
