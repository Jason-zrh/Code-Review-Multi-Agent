# Code Review Multi-Agent

> 基于 LangGraph Multi-Agent 架构的 AI 代码审查系统

## 项目状态

**状态**：Phase 1 开发中

## 快速开始

```bash
# 安装依赖
python3.11 -m pip install -r requirements.txt

# 运行服务
python3.11 -m uvicorn src.main:app --reload

# 运行测试
python3.11 -m pytest tests/ -v
```

## 技术栈

| 层级 | 技术 |
|------|------|
| Multi-Agent 框架 | LangGraph |
| API 框架 | FastAPI |
| 消息队列 | Redis Streams（后续） |
| 容器化 | Docker |

## 项目结构

```
Code-Review-Agent/
├── src/
│   ├── main.py              # FastAPI 应用入口
│   ├── models/schemas.py    # 数据模型（PR、审查结果）
│   ├── github/webhook.py    # GitHub Webhook 验证和解析
│   ├── coordinator/workflow.py  # LangGraph 工作流
│   └── api/routes.py        # API 路由定义
├── tests/                   # 测试
├── config/settings.py       # 配置
├── requirements.txt
└── Dockerfile
```

## 开发计划

- [x] Phase 1.1：项目初始化（基础结构、模型、Webhook、工作流）
- [ ] Phase 1.2：GitHub API 接入、LLM 代码分析、PR 评论
- [ ] Phase 2：Multi-Agent 并行执行
