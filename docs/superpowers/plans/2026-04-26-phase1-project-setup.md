# Phase 1: 项目初始化 - 实施计划

> **Goal:** 搭建项目基础结构，FastAPI + LangGraph 集成，GitHub Webhook 接收接口

**Architecture:**
- FastAPI 提供 Webhook 接收端点
- LangGraph 定义简单的状态机工作流
- 项目结构按照规划分离各层（agents/coordinator/github）

**Tech Stack:** Python 3.11+, FastAPI, LangGraph, uvicorn, httpx

---

## 项目文件结构

```
Code-Review-Agent/
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   └── code_reviewer.py       # 单 Agent 实现（Phase 1）
│   ├── coordinator/
│   │   ├── __init__.py
│   │   └── workflow.py           # LangGraph 状态机定义
│   ├── github/
│   │   ├── __init__.py
│   │   ├── webhook.py           # Webhook 接收与验证
│   │   └── client.py            # GitHub API 客户端
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # 数据模型（PR、Review 结果）
│   └── api/
│       ├── __init__.py
│       └── routes.py            # FastAPI 路由定义
├── tests/
│   ├── __init__.py
│   ├── test_webhook.py
│   ├── test_code_reviewer.py
│   └── test_workflow.py
├── config/
│   └── settings.py              # 配置管理
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Task 1: 创建项目基础结构

**Files:**
- Create: `src/__init__.py`, `src/agents/__init__.py`, `src/coordinator/__init__.py`, `src/github/__init__.py`, `src/models/__init__.py`, `src/api/__init__.py`, `tests/__init__.py`

- [ ] **Step 1: 创建目录**

```bash
mkdir -p src/agents src/coordinator src/github src/models src/api tests config
touch src/__init__.py src/agents/__init__.py src/coordinator/__init__.py src/github/__init__.py src/models/__init__.py src/api/__init__.py tests/__init__.py
```

- [ ] **Step 2: 创建 requirements.txt**

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
langgraph==0.2.0
langchain-core==0.3.0
langchain-openai==0.2.0
httpx==0.27.0
pydantic==2.6.0
python-dotenv==1.0.0
```

- [ ] **Step 3: 创建 config/settings.py**

```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """项目配置"""

    # GitHub 配置
    github_webhook_secret: str = "your-webhook-secret"
    github_token: Optional[str] = None

    # Redis 配置
    redis_url: str = "redis://localhost:6379"

    # LLM 配置
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

---

## Task 2: 数据模型定义

**Files:**
- Create: `src/models/schemas.py`
- Test: `tests/test_schemas.py`

- [ ] **Step 1: 创建 tests/test_schemas.py**

```python
from src.models.schemas import PullRequest, FileChange, ReviewResult, ReviewComment


def test_pull_request_model():
    """测试 PR 模型序列化"""
    pr = PullRequest(
        pr_id=123,
        repo_owner="test-owner",
        repo_name="test-repo",
        title="Fix login bug",
        description="Fixed null pointer exception",
    )
    data = pr.model_dump()
    assert data["pr_id"] == 123
    assert data["repo_owner"] == "test-owner"


def test_file_change_model():
    """测试文件变更模型"""
    change = FileChange(
        filename="src/auth.py",
        status="modified",
        additions=10,
        deletions=5,
        patch="@@ -1,5 +1,10 @@",
    )
    assert change.filename == "src/auth.py"
    assert change.status == "modified"


def test_review_result_model():
    """测试审查结果模型"""
    result = ReviewResult(
        pr_id=123,
        overall_status="success",
        comments=[
            ReviewComment(
                file="src/auth.py",
                line=42,
                severity="warning",
                category="bug",
                message="Potential null pointer",
            )
        ],
    )
    assert len(result.comments) == 1
    assert result.comments[0].severity == "warning"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_schemas.py -v`
Expected: FAIL - `ImportError: No module named 'src.models'`

- [ ] **Step 3: 创建 src/models/schemas.py**

```python
from pydantic import BaseModel
from typing import Optional


class PullRequest(BaseModel):
    """Pull Request 模型"""

    pr_id: int
    repo_owner: str
    repo_name: str
    title: str
    description: str
    author: Optional[str] = None


class FileChange(BaseModel):
    """文件变更模型"""

    filename: str
    status: str  # "added", "modified", "removed"
    additions: int = 0
    deletions: int = 0
    patch: Optional[str] = None


class ReviewComment(BaseModel):
    """审查评论模型"""

    file: str
    line: Optional[int] = None
    severity: str  # "info", "warning", "error", "critical"
    category: str  # "bug", "security", "style", "performance"
    message: str


class ReviewResult(BaseModel):
    """审查结果模型"""

    pr_id: int
    overall_status: str  # "success", "failed"
    summary: Optional[str] = None
    comments: list[ReviewComment] = []
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add data models for PR, FileChange, ReviewResult"
```

---

## Task 3: GitHub Webhook 接收与验证

**Files:**
- Create: `src/github/webhook.py`
- Modify: `src/api/routes.py`
- Test: `tests/test_webhook.py`

- [ ] **Step 1: 创建 tests/test_webhook.py**

```python
import hmac
import hashlib
import json
from src.github.webhook import verify_webhook_signature, parse_github_event


def test_verify_webhook_signature_valid():
    """测试有效的 Webhook 签名"""
    secret = "test-secret"
    payload = b'{"action": "opened"}'
    signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    result = verify_webhook_signature(payload, f"sha256={signature}", secret)
    assert result is True


def test_verify_webhook_signature_invalid():
    """测试无效的 Webhook 签名"""
    secret = "test-secret"
    payload = b'{"action": "opened"}'
    wrong_signature = "sha256=invalid"

    result = verify_webhook_signature(payload, wrong_signature, secret)
    assert result is False


def test_parse_github_pr_event():
    """测试解析 GitHub PR 事件"""
    payload = {
        "action": "opened",
        "pull_request": {
            "id": 123,
            "title": "Fix bug",
            "body": "Description",
            "user": {"login": "testuser"},
        },
        "repository": {
            "owner": {"login": "owner"},
            "name": "repo",
        },
    }
    event = parse_github_event("pull_request", payload)
    assert event["action"] == "opened"
    assert event["pr"]["id"] == 123
    assert event["pr"]["title"] == "Fix bug"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_webhook.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'src.github'`

- [ ] **Step 3: 创建 src/github/webhook.py**

```python
import hmac
import hashlib
from typing import Any
from config.settings import settings


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str = None
) -> bool:
    """验证 GitHub Webhook 签名"""
    if secret is None:
        secret = settings.github_webhook_secret

    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)


def parse_github_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """解析 GitHub 事件"""
    if event_type == "pull_request":
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})
        return {
            "action": payload.get("action"),
            "pr": {
                "id": pr.get("id"),
                "title": pr.get("title"),
                "description": pr.get("body"),
                "author": pr.get("user", {}).get("login"),
            },
            "repo": {
                "owner": repo.get("owner", {}).get("login"),
                "name": repo.get("name"),
            },
        }
    return {"action": payload.get("action")}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_webhook.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add GitHub webhook verification and parsing"
```

---

## Task 4: LangGraph 状态机定义

**Files:**
- Create: `src/coordinator/workflow.py`
- Test: `tests/test_workflow.py`

- [ ] **Step 1: 创建 tests/test_workflow.py**

```python
from src.coordinator.workflow import CodeReviewWorkflow, ReviewState


def test_review_state_initialization():
    """测试状态初始化"""
    state = ReviewState(
        pr_id=123,
        repo_owner="owner",
        repo_name="repo",
        files=[],
    )
    assert state.pr_id == 123
    assert state.review_comments == []


def test_workflow_initialization():
    """测试工作流初始化"""
    workflow = CodeReviewWorkflow()
    assert workflow.graph is not None
    assert workflow.app is not None


def test_workflow_run():
    """测试工作流执行"""
    workflow = CodeReviewWorkflow()
    result = workflow.run(
        pr_id=123,
        repo_owner="owner",
        repo_name="repo",
        files=[],
    )
    assert result["overall_status"] == "success"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_workflow.py -v`
Expected: FAIL - `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/coordinator/workflow.py**

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from src.models.schemas import ReviewComment


class ReviewState(TypedDict):
    """审查状态"""

    pr_id: int
    repo_owner: str
    repo_name: str
    files: list
    review_comments: list[ReviewComment]
    overall_status: str


class CodeReviewWorkflow:
    """代码审查工作流"""

    def __init__(self):
        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        builder = StateGraph(ReviewState)

        # 添加入口节点
        builder.add_node("start", self._node_start)
        builder.add_node("analyze", self._node_analyze)
        builder.add_node("finish", self._node_finish)

        builder.set_entry_point("start")
        builder.add_edge("start", "analyze")
        builder.add_edge("analyze", "finish")
        builder.add_edge("finish", END)

        return builder

    def _node_start(self, state: ReviewState) -> ReviewState:
        """开始节点"""
        return state

    def _node_analyze(self, state: ReviewState) -> ReviewState:
        """分析节点（Phase 1 单 Agent）"""
        state["review_comments"] = []
        return state

    def _node_finish(self, state: ReviewState) -> ReviewState:
        """完成节点"""
        state["overall_status"] = "success"
        return state

    def run(
        self,
        pr_id: int,
        repo_owner: str,
        repo_name: str,
        files: list,
    ) -> dict:
        """运行工作流"""
        initial_state = ReviewState(
            pr_id=pr_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            files=files,
            review_comments=[],
            overall_status="pending",
        )
        result = self.app.invoke(initial_state)
        return result
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_workflow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add LangGraph workflow with state machine"
```

---

## Task 5: FastAPI 路由集成

**Files:**
- Create: `src/api/routes.py`
- Create: `src/main.py`
- Test: `tests/test_routes.py`

- [ ] **Step 1: 创建 tests/test_routes.py**

```python
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_webhook_endpoint_missing_signature():
    """测试 Webhook 端点 - 缺少签名"""
    response = client.post(
        "/webhook",
        json={"action": "opened"},
    )
    assert response.status_code == 401


def test_webhook_endpoint_invalid_signature():
    """测试 Webhook 端点 - 无效签名"""
    response = client.post(
        "/webhook",
        json={"action": "opened"},
        headers={"X-Hub-Signature-256": "sha256=invalid"},
    )
    assert response.status_code == 401
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_routes.py -v`
Expected: FAIL - `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/api/routes.py**

```python
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from src.github.webhook import verify_webhook_signature, parse_github_event
from src.coordinator.workflow import CodeReviewWorkflow


router = APIRouter()
workflow = CodeReviewWorkflow()


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
):
    """GitHub Webhook 端点"""
    payload = await request.body()

    # 验证签名（生产环境应启用）
    if x_hub_signature_256:
        if not verify_webhook_signature(payload, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "")

    if event_type == "pull_request":
        event = parse_github_event(event_type, data)
        if event.get("action") in ["opened", "synchronize"]:
            # 触发审查
            result = workflow.run(
                pr_id=event["pr"]["id"],
                repo_owner=event["repo"]["owner"],
                repo_name=event["repo"]["name"],
                files=[],
            )
            return {"status": "ok", "result": result}

    return {"status": "ignored"}
```

- [ ] **Step 4: 创建 src/main.py**

```python
from fastapi import FastAPI
from src.api.routes import router
from config.settings import settings


app = FastAPI(
    title="Code Review Multi-Agent",
    description="AI-powered code review system with Multi-Agent architecture",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_routes.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: add FastAPI routes and webhook integration"
```

---

## Task 6: Docker 配置

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: 创建 Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 创建 docker-compose.yml**

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - .:/app

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

- [ ] **Step 3: 创建 .env.example**

```
GITHUB_WEBHOOK_SECRET=your-webhook-secret
GITHUB_TOKEN=ghp_your_token
OPENAI_API_KEY=sk-your-key
REDIS_URL=redis://localhost:6379
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: add Docker configuration"
```

---

## 实施检查清单

- [ ] 项目结构创建完成
- [ ] 数据模型通过测试
- [ ] Webhook 验证通过测试
- [ ] LangGraph 工作流通过测试
- [ ] API 路由通过测试
- [ ] Docker 配置完成
- [ ] 所有测试通过

---

## 下一步（Phase 1.2）

1. 实现 GitHub API 客户端获取 PR diff
2. 实现单 Agent 代码分析逻辑
3. 实现结果评论到 GitHub PR
4. 创建测试仓库验证完整流程
