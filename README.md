# Code Review Multi-Agent

> 基于 LangGraph Multi-Agent 架构的 AI 代码审查系统

自动分析 GitHub Pull Requests，通过专门的 AI Agent 检测安全漏洞、代码 Bug 和风格问题，并将审查结果直接评论到 PR 上。

## 功能特性

- **自动化代码审查** - GitHub PR 事件自动触发
- **Multi-Agent 架构** - 专门的 Agent 并行运行
- **Router Agent** - 分类文件并路由到对应 Agent
- **Security Agent** - 检测 SQL 注入、命令注入、硬编码密钥、路径遍历
- **Bug Agent** - 检测空指针、除零错误、数组越界、逻辑错误
- **Style Agent** - 检测缺失文档、命名不规范、代码格式问题
- **Aggregator Agent** - 合并并汇总所有 Agent 的结果
- **并行执行** - 基于 LangGraph 的高效工作流
- **GitHub 集成** - 直接在 PR 上发布审查评论

## 技术栈

| 层级 | 技术 |
|------|------|
| Multi-Agent 框架 | LangGraph |
| LLM | MiniMax API (OpenAI-compatible) |
| API 框架 | FastAPI |
| HTTP 客户端 | httpx |
| 数据验证 | Pydantic |
| 测试框架 | pytest |
| 容器化 | Docker |

## 项目结构

```
Code-Review-Agent/
├── src/
│   ├── main.py                    # FastAPI 入口
│   ├── models/schemas.py          # 数据模型 (Pydantic)
│   ├── github/
│   │   ├── webhook.py             # Webhook 验证和解析
│   │   └── client.py              # GitHub API 客户端
│   ├── coordinator/
│   │   └── workflow.py            # LangGraph 工作流
│   ├── agents/
│   │   ├── router_agent.py        # 文件分类
│   │   ├── security_agent.py      # 安全分析
│   │   ├── bug_agent.py           # Bug 检测
│   │   ├── style_agent.py         # 风格分析
│   │   └── aggregator_agent.py    # 结果汇总
│   └── api/routes.py              # API 路由
├── tests/                         # 36 个测试用例
├── docs/                          # 设计文档
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 快速开始

### 前置要求

- Python 3.11+
- GitHub Personal Access Token
- MiniMax / OpenAI API Key

### 安装

```bash
git clone <仓库地址>
cd Code-Review-Agent
python3.11 -m pip install -r requirements.txt
```

### 配置

创建 `.env` 文件：

```bash
# GitHub 配置
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# LLM API 配置（支持 MiniMax 或 OpenAI 兼容接口）
OPENAI_API_KEY=xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.minimaxi.com/v1
```

### 选择部署方式

根据你的场景选择以下一种部署方式：

> **重要说明**：Webhook 配置和怎么运行服务无关。关键是 **GitHub 必须能访问到你的服务地址**。
>
> - **本地电脑**：GitHub 无法访问你的 localhost，必须用 ngrok
> - **云服务器**：GitHub 可以访问服务器 IP，Webhook 直接指向服务器地址

---

## 方式一：云服务器部署（推荐）

适用于：有公网 IP 的服务器，长期运行

### 运行

选择任意一种启动方式：

**方式 A：直接运行**
```bash
python3.11 -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**方式 B：Docker 运行**
```bash
docker-compose up -d
docker-compose logs -f   # 查看日志
```

### 配置 GitHub Webhook

1. 确保服务器防火墙开放 8000 端口
2. 配置 Webhook：
```bash
gh api repos/{owner}/{repo}/hooks -X POST \
  -F url="http://你的服务器IP:8000/webhook" \
  -F events[]=pull_request
```
3. 测试：创建或更新 PR 触发审查
```bash
gh pr create --title "Test PR" --body "Testing webhook"
```

---

## 方式二：本地调试

适用于：在本地电脑开发调试

> ⚠️ **关键限制**：GitHub 无法访问你的 localhost，所以必须用 ngrok 打通网络

### 运行

1. 启动服务（二选一）：
```bash
# 方式 A：直接运行
python3.11 -m uvicorn src.main:app --reload --port 8000

# 方式 B：Docker 运行
docker-compose up
```

2. 启动 ngrok 暴露公网地址：
```bash
ngrok http 8000
```

3. 配置 Webhook（使用 ngrok 提供的临时 URL，如 `https://xxxx.ngrok.io/webhook`）

> 注意：ngrok 免费版每次重启 URL 会变，不适合长期使用

## 架构设计

### Multi-Agent 工作流

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub PR                               │
│                  (opened / synchronize)                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           Route                                 │
│                    (Security/Bug/Style)                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Security Agent  │ │    Bug Agent    │ │   Style Agent   │
│                 │ │                 │ │                 │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    A. ggregate Node                             │
│                                                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Post Comments Node                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 检测能力

| 类别 | 检测问题 |
|------|---------|
| 安全 | SQL 注入、命令注入、路径遍历、硬编码密钥、硬编码密码 |
| Bug | 空指针、除零错误、数组越界、逻辑错误 |
| 风格 | 缺失文档、命名不规范、尾部注释、未使用变量 |


## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行并查看覆盖率
pytest tests/ --cov=src --cov-report=term-missing
```

## 技术挑战与解决方案

| 问题 | 解决方案 |
|------|---------|
| PR ID vs Number | GitHub API 使用 PR 编号，不是全局 ID |
| Commit SHA | 从 PR 详情获取实际 SHA，而非 "HEAD" |
| 空文件评论 | 跳过没有有效 patch 的文件 |
| 行号越界 | 将 LLM 生成的行号限制在文件范围内 |
| HTTP 超时 | 添加 30 秒超时和 3 次重试 |
| 状态合并 | 使用自定义 reducer 合并 LangGraph 并行节点 |



## 后续规划

详见 [docs/FUTURE.md](docs/FUTURE.md)：
- Webhook 签名验证
- 数据库存储（审查历史）
- Markdown 汇总报告
- 多仓库支持
- C++ 静态分析
- 消息队列（Redis）
- GitHub App 集成       