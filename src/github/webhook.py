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
