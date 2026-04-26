from src.github.client import GitHubClient


def test_github_client_initialization():
    """测试客户端初始化"""
    client = GitHubClient(token="test-token")
    assert client.token == "test-token"


def test_github_client_with_settings_token():
    """测试客户端使用配置中的 token"""
    from config.settings import settings
    client = GitHubClient()
    # 应该从 settings 读取
    assert client.token == settings.github_token


def test_get_pr_files_method_exists():
    """测试方法存在"""
    client = GitHubClient(token="test-token")
    assert hasattr(client, "get_pr_files")
    assert hasattr(client, "get_pr_details")
    assert hasattr(client, "create_review_comment")
    assert hasattr(client, "create_pr_review")