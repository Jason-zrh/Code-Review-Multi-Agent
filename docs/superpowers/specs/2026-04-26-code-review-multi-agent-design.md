# Code Review Multi-Agent 项目设计

> 创建时间：2026/04/26

## 项目定位

基于 Multi-Agent 架构的 AI 代码审查系统，自动分析 GitHub PR，给出多维度反馈（Bug 检测、安全漏洞、代码风格）并评论到 PR 上。

## 技术栈

| 层级 | 选择 | 说明 |
|------|------|------|
| Multi-Agent 框架 | LangGraph | LangChain 官方推荐的 Multi-Agent 编排方案，行业趋势 |
| GitHub 接入 | Webhook | Phase 1 最简方案，后续升级到 GitHub App |
| 消息队列 | Redis Streams | 支持消费组、ACK 机制，部署简单 |
| API 框架 | FastAPI | 现代化 Python 框架，自动生成 API 文档 |
| 容器化 | Docker | 统一环境，便于部署和扩展 |
| 数据库 | MySQL | Phase 1 数据存储，标准关系型数据库 |

## Phase 1 目标

### 核心流程
```
GitHub PR 触发 Webhook
    ↓
FastAPI 接收请求
    ↓
单 Agent 分析代码（Bug + Security + Style 混合）
    ↓
生成审查结果
    ↓
评论到 GitHub PR
```

### 交付目标
- GitHub Webhook 接入（PR 事件触发）
- 单 Agent 完成代码分析
- 结果评论到 GitHub PR
- 独立测试仓库验证

### 后续扩展路径
1. 拆成 Bug/Security/Style 多个 Agent 并行执行
2. Summary Agent 汇总结果
3. C++ 静态分析规则引擎（确定性检测 + AI 二次验证）
4. 升级到 GitHub App

## 测试环境

新建独立测试仓库 `code-review-test`，包含有问题的示例代码用于验证审查效果。

## 关键设计决策

1. **LangGraph vs LangChain**：选择 LangGraph，体现对最新工具的掌握
2. **Webhook vs GitHub App**：Phase 1 用 Webhook 快速验证，后续升级
3. **Redis Streams vs Kafka**：Redis 更轻量，适合 Phase 1
4. **纯 LLM vs C++ 引擎**：Phase 1 先纯 LLM，C++ 引擎后续扩展
