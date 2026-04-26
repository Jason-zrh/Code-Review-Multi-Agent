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
