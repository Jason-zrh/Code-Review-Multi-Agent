# Code Review Multi-Agent

> 基于 LangGraph Multi-Agent 架构的 AI 代码审查系统

## 项目状态

**Phase 1 已完成** ✅

## 已完成功能

### Phase 1.1 - 项目初始化 ✅
- [x] 基础项目结构
- [x] 数据模型（PR、审查结果）
- [x] 配置管理

### Phase 1.2 - GitHub 集成 ✅ (2026-04-26)
- [x] GitHub Webhook 接收和验证
- [x] PR 事件解析（修复 PR number 问题）
- [x] PR 文件获取
- [x] LLM 代码分析（MiniMax API 集成）
- [x] PR 评论发布（修复空文件、行号验证问题）

### 已修复的 Bug
1. **PR ID 问题** - GitHub API 需要 PR 编号而非全局 ID
2. **Commit SHA 问题** - 需要实际 commit SHA 而非 "HEAD"
3. **空文件评论问题** - 跳过无有效 patch 的文件
4. **行号越界问题** - 验证 LLM 生成的行号在文件范围内

## 快速开始

```bash
# 安装依赖
python3.11 -m pip install -r requirements.txt

# 启动 ngrok（用于接收 GitHub Webhook）
ngrok http 8000

# 运行服务
python3.11 -m uvicorn src.main:app --reload --port 8000

# 配置 GitHub Webhook
gh api repos/{owner}/{repo}/hooks -X POST -F url="{ngrok_url}/webhook" -F events[]=pull_request
```

## 技术栈

| 层级 | 技术 |
|------|------|
| Multi-Agent 框架 | LangGraph |
| LLM | MiniMax API (OpenAI-compatible) |
| API 框架 | FastAPI |
| 消息队列 | Redis Streams（后续） |
| 容器化 | Docker |

## 项目结构

```
Code-Review-Agent/
├── src/
│   ├── main.py              # FastAPI 应用入口
│   ├── models/schemas.py    # 数据模型（PR、审查结果）
│   ├── github/
│   │   ├── webhook.py       # GitHub Webhook 验证和解析
│   │   └── client.py        # GitHub API 客户端
│   ├── coordinator/
│   │   └── workflow.py      # LangGraph 工作流（单 Agent）
│   ├── agents/
│   │   └── code_reviewer.py # LLM 代码审查 Agent
│   ├── api/
│   │   └── routes.py        # API 路由定义
│   └── config/
│       └── settings.py       # 配置管理
├── tests/                   # 测试
├── requirements.txt
└── Dockerfile
```

## 工作流程

```
GitHub PR Event (synchronize/opened)
    ↓
Webhook 验证签名 + 解析事件
    ↓
获取 PR 文件列表
    ↓
LLM 代码分析（Security、Bug、Style）
    ↓
验证评论行号（跳过空文件、限制行号范围）
    ↓
发布评论到 GitHub PR
```

## 开发计划

- [x] Phase 1.1：项目初始化（基础结构、模型、Webhook、工作流）
- [x] Phase 1.2：GitHub API 接入、LLM 代码分析、PR 评论
- [ ] Phase 2：Multi-Agent 并行执行
  - [ ] Router Agent（任务分类）
  - [ ] Security Agent（安全审查）
  - [ ] Bug Agent（Bug 检测）
  - [ ] Style Agent（代码风格）
  - [ ] 汇总 Agent（整合结果）

## 配置

环境变量或 `.env` 文件：

```bash
GITHUB_TOKEN=ghp_xxx          # GitHub Personal Access Token
OPENAI_API_KEY=sk-xxx         # MiniMax API Key
OPENAI_BASE_URL=https://api.minimaxi.com/v1
REDIS_URL=redis://localhost:6379
```
