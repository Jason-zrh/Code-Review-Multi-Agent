from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from src.github.webhook import verify_webhook_signature, parse_github_event
from src.coordinator.workflow import CodeReviewWorkflow


# ============================================================
# API 路由层
# 作用：定义 HTTP 接口，接收外部请求
# 入口：GitHub Webhook POST /webhook
# ============================================================

router = APIRouter()
workflow = CodeReviewWorkflow()


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
):
    """GitHub Webhook 端点

    接收 GitHub 推送的事件，验证签名后触发代码审查流程

    Headers:
        X-Hub-Signature-256: GitHub 签名（可选，测试环境可跳过）
        X-GitHub-Event: 事件类型（pull_request, push, ...）

    Body:
        GitHub 发送的完整 JSON 数据
    """
    # 获取请求体原始字节
    payload = await request.body()

    # 验证签名：防止伪造请求（生产环境应启用）
    if x_hub_signature_256:
        if not verify_webhook_signature(payload, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # 解析 JSON 和事件类型
    data = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "")

    # 只处理 PR 事件（opened=新建 PR，synchronize=更新 PR）
    if event_type == "pull_request":
        event = parse_github_event(event_type, data)
        if event.get("action") in ["opened", "synchronize"]:
            # 触发 Multi-Agent 审查流程
            result = workflow.run(
                pr_id=event["pr"]["id"],
                repo_owner=event["repo"]["owner"],
                repo_name=event["repo"]["name"],
                files=[],
            )
            return {"status": "ok", "result": result}

    return {"status": "ignored"}
