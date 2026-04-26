import hmac
import hashlib
from typing import Any
from config.settings import settings


# ============================================================
# GitHub Webhook 处理层
# 作用：接收并验证 GitHub 推送的事件
# 安全性：通过 HMAC-SHA256 签名验证防止伪造请求
# ============================================================

def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str = None
) -> bool:
    """验证 GitHub Webhook 签名

    GitHub 发请求时会带 X-Hub-Signature-256 头
    我们用同样的算法算一遍，比较结果防止伪造

    Args:
        payload: 请求体原始字节
        signature: GitHub 发的签名 "sha256=xxxxx"
        secret: 密钥，默认从配置读取

    Returns:
        签名匹配返回 True，否则返回 False
    """
    if secret is None:
        secret = settings.github_webhook_secret

    # HMAC-SHA256：一种安全的消息认证码算法
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # timing-safe 比较：防止时序攻击（黑客通过比较时间猜密钥）
    return hmac.compare_digest(f"sha256={expected}", signature)


def parse_github_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """解析 GitHub 事件

    GitHub 发来的 JSON 很长，我们只提取需要的字段

    Args:
        event_type: 事件类型（如 pull_request, push, issue）
        payload: GitHub 发的完整 JSON 数据

    Returns:
        简化后的事件数据字典
    """
    if event_type == "pull_request":
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})
        return {
            "action": payload.get("action"),
            "pr": {
                # BUG FIX: GitHub API 使用 PR number 而不是内部全局 ID
                # GitHub webhook payload 中 pull_request.id 是全局唯一整数（如 3585522396）
                # 但 GET /repos/{owner}/{repo}/pulls/{number}/files 需要的是 PR 编号（如 2）
                # 使用 id 而非 number 会导致 404 错误
                "id": pr.get("number"),
                "title": pr.get("title"),
                "description": pr.get("body"),
                "author": pr.get("user", {}).get("login"),
            },
            "repo": {
                "owner": repo.get("owner", {}).get("login"),
                "name": repo.get("name"),
            },
        }
    # 非 pull_request 事件只返回 action
    return {"action": payload.get("action")}
