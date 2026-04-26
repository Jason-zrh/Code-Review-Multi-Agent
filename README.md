# Code Review Multi-Agent

> 基于 Multi-Agent 架构的 AI 代码审查系统

## 项目状态

**状态**：规划中

## 项目简介

本项目旨在构建一个 Multi-Agent 代码审查系统，能够自动分析 GitHub PR，从 Bug 检测、安全漏洞、代码风格等多个维度给出专业反馈。

## 核心特性

- 🤖 **Multi-Agent 协作**：协调者 + 专业审查 Agent 分层设计
- 🔍 **多维度审查**：Bug、安全、风格、性能、架构
- 🔗 **GitHub 集成**：Webhook 自动触发，PR 下自动评论
- 📊 **可视化报告**：按严重程度排序，引用具体代码行

## 技术栈

- Python (LangChain Multi-Agent)
- C++ (静态分析规则引擎)
- Docker
- FastAPI
- Redis (消息队列)

## 文档

- [项目规划](PROJECT_PLAN.md) - 详细架构设计
- [对话记录](CONVERSATION_LOG.md) - 项目决策过程
