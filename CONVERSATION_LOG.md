# 项目对话记录

## 用户背景

- C++ 后端开发方向大二学生
- 已完成 Multi-Agent 开发（coordinator + searcher 模式）
- 已掌握：LangChain Agent、Tool Calling、RAG + FAISS、短期/长期记忆

## 项目需求演变

### 最初需求
用户问："我现在的知识够不够做简历项目"

### 第一次推荐
给出三个经典项目方向：
1. RAG 智能知识库问答系统
2. Multi-Agent 智能任务助手
3. Code Review AI Agent

### 用户反馈
用户表示这些"有点烂大街"，想要更新鲜的创意

### 新推荐方向
1. AI Agent 评测平台
2. Codebase-Aware RAG
3. Multi-Agent Code Translation
4. Autonomous DevOps Agent

### 用户选择
用户选择了 **Code Review AI Agent**，并问："能不能用 Multi-Agent"

### 最终确认
确定采用 **Multi-Agent Code Review** 架构

## 核心架构确定

```
Coordinator (协调者)
    ├── Bug Agent (Bug检测)
    ├── Security Agent (安全漏洞)
    ├── Style Agent (代码风格)
    ├── Performance Agent (性能问题) [可选]
    ├── Architecture Agent (架构设计) [可选]
    └── Summary Agent (汇总报告)
```

## 关键技术决策

1. **Multi-Agent 协作模式**：每个 Agent 专业化，并行执行
2. **C++ 背景利用**：静态分析规则引擎用 C++ 写
3. **Phase 1**：先用单一 Agent 跑通流程
4. **Phase 2**：拆分成 Multi-Agent

## 简历定位

> 设计并实现 Multi-Agent 协作的代码审查系统，接入 GitHub Webhook 自动分析 PR

## 下一步

等待用户确认后，提供按天拆的详细开发计划
