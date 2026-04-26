# ============================================================
# Webhook 测试
# 测试 GitHub 签名验证和事件解析
# ============================================================

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
