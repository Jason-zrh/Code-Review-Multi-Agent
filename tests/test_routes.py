# ============================================================
# API 路由测试
# 测试 /webhook 和 /health 端点
# ============================================================

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
    # 当没有签名头时，验证被跳过，请求正常处理
    assert response.status_code == 200


def test_webhook_endpoint_pull_request_opened():
    """测试 Webhook 端点 - PR 打开事件"""
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
    response = client.post(
        "/webhook",
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
