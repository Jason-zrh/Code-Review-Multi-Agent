# Code Review Multi-Agent - 设计文档


## 1. 项目概述

**Code Review Multi-Agent** 是一个基于 AI 的代码审查系统，通过 GitHub Webhook 自动接收 Pull Request 事件，使用专门的 AI Agent 并行分析代码安全问题、Bug 和代码风格，并将审查结果直接评论到 PR 上。

## 2. 技术选型

| 层级 | 技术 | 选择理由 |
|------|------|----------|
| Agent 框架 | LangGraph | 原生支持 Multi-Agent 编排，内置状态管理和条件路由 |
| LLM | MiniMax API | OpenAI 兼容接口，成本低 |
| Web 框架 | FastAPI | 异步支持，自动生成 API 文档 |
| HTTP 客户端 | httpx | 异步请求，超时和重试支持 |
| 数据验证 | Pydantic | 类型安全，自动序列化 |
| 测试框架 | pytest | Python 标准测试框架 |

## 3. 架构设计

### 3.1 Multi-Agent 工作流

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub PR                                │
│                    (opened / synchronize)                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Route Node                               │
│                    (RouterAgent 分类文件)                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Security Agent  │ │   Bug Agent     │ │  Style Agent    │
│   (并行执行)     │ │   (并行执行)     │ │   (并行执行)     │
│                 │ │                 │ │                 │
│ • SQL 注入      │ │ • 空指针        │ │ • 缺失文档     │
│ • 命令注入      │ │ • 除零错误      │ │ • 命名不规范   │
│ • 路径遍历      │ │ • 数组越界      │ │ • 代码格式     │
│ • 硬编码密钥    │ │ • 逻辑错误      │ │                │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
              ┌─────────────────────────────┐
              │      Aggregate Node         │
              │    (AggregatorAgent 汇总)    │
              └─────────────┬───────────────┘
                            ▼
              ┌─────────────────────────────┐
              │     Post Comments Node       │
              │   (发布到 GitHub PR)         │
              └─────────────────────────────┘
```

### 3.2 状态管理

使用 LangGraph `TypedDict` 定义工作流状态，并行节点结果通过自定义 reducer 合并：

```python
class ReviewState(TypedDict):
    pr_id: int                           # PR 编号
    repo_owner: str                      # 仓库所有者
    repo_name: str                       # 仓库名
    files: list                          # 改动的文件列表
    routes: dict                         # 路由结果
    agent_results: Annotated[dict, _merge_agent_results]  # 并行节点结果
    review_comments: list                # 审查评论
    overall_status: str                  # 总体状态
```

### 3.3 Agent 设计

| Agent | 职责 | 检测问题 |
|-------|------|----------|
| RouterAgent | 根据文件类型分类应该用哪些 Agent 审查 | - |
| SecurityAgent | 安全漏洞检测 | SQL 注入、命令注入、路径遍历、XSS、硬编码密钥 |
| BugAgent | Bug 检测 | 空指针、除零错误、数组越界、逻辑错误 |
| StyleAgent | 代码风格分析 | 缺失文档、命名不规范、代码格式 |
| AggregatorAgent | 汇总所有结果 | 生成摘要，确定总体状态 |

## 4. 目录结构

```
Code-Review-Agent/
├── src/
│   ├── main.py                    # FastAPI 入口
│   ├── api/
│   │   └── routes.py             # API 路由 (/webhook)
│   ├── models/
│   │   └── schemas.py            # Pydantic 数据模型
│   ├── github/
│   │   ├── client.py            # GitHub API 客户端
│   │   └── webhook.py           # Webhook 签名验证
│   ├── coordinator/
│   │   └── workflow.py          # LangGraph 工作流
│   └── agents/
│       ├── router_agent.py      # 路由 Agent
│       ├── security_agent.py    # 安全 Agent
│       ├── bug_agent.py        # Bug Agent
│       ├── style_agent.py       # 风格 Agent
│       └── aggregator_agent.py  # 聚合 Agent
├── tests/                        # 测试用例
├── docs/                         # 文档
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 5. 关键技术决策

### 5.1 LangGraph vs LangChain

选择 LangGraph 而非纯 LangChain：
- 原生支持 Multi-Agent 编排
- 内置状态管理和 Reducer
- 条件边支持 Fan-out/Fan-in 模式
- 生产级 Agent 工作流支持

### 5.2 Webhook vs GitHub App

当前使用 Webhook，Phase 3 可升级为 GitHub App：

| 特性 | Webhook | GitHub App |
|------|---------|------------|
| 安装 | 每个仓库单独配置 | 一次安装，所有仓库生效 |
| ngrok | 需要（本地开发） | 不需要 |
| 权限 | 全部读写 | 精细控制 |

### 5.3 状态合并策略

并行 Agent 节点使用自定义 Reducer 合并结果：

```python
def _merge_agent_results(left: dict, right: dict) -> dict:
    """合并并行节点结果，避免双重包装"""
    result = {}
    for key, value in chain(left.items(), right.items()):
        if key == "agent_results" and isinstance(value, dict):
            for agent_name, agent_data in value.items():
                if agent_name not in result:
                    result[agent_name] = agent_data
                elif isinstance(agent_data, list):
                    result[agent_name] = result.get(agent_name, []) + agent_data
        else:
            result[key] = value
    return result
```

## 6. 已知问题与解决

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `'str' object has no attribute 'get'` | 状态合并返回嵌套字典 | 直接返回合并结果，不包装 |
| GitHub API 超时 | 未配置超时 | 添加 30 秒超时 + 3 次重试 |
| `state['routes']` 为 None | LangGraph 状态更新时机 | 默认使用所有 Agent |
| PR ID vs Number 混淆 | GitHub API 使用不同 ID | 使用 PR 编号调用 API |
| Commit SHA 无效 | "HEAD" 不是有效 SHA | 从 PR 详情获取实际 SHA |
| 空文件评论 | GitHub API 拒绝空 diff 评论 | 跳过无有效 patch 的文件 |
| 行号越界 | LLM 可能生成无效行号 | 将行号限制在文件范围内 |

## 7. 测试覆盖

| 测试文件 | 覆盖内容 |
|----------|----------|
| test_workflow.py | 工作流状态管理、路由逻辑 |
| test_router_agent.py | 文件分类逻辑 |
| test_specialized_agents.py | Security/Bug/Style Agent |
| test_aggregator_agent.py | 结果聚合 |
| test_github_client.py | GitHub API 客户端 |
| test_schemas.py | Pydantic 模型验证 |
| test_routes.py | API 端点行为 |

## 8. 当前限制

1. **Webhook 签名验证**：已实现但默认关闭（本地测试用）
2. **单仓库支持**：当前配置适用于单个仓库
3. **无数据库**：审查历史未持久化
4. **同步处理**：无消息队列处理突发流量

## 9. Phase 规划

| Phase | 状态 | 说明 |
|-------|------|------|
| Phase 1 | ✅ 已完成 | 基础 GitHub 集成，单 Agent |
| Phase 2 | ✅ 已完成 | Multi-Agent 并行架构 |
| Phase 3 | 规划中 | Webhook 验证、数据库、报告、多仓库 |