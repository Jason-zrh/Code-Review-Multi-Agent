import httpx
from typing import Optional


# ============================================================
# GitHub API 客户端
# 作用：封装 GitHub REST API，提供语义化的方法调用
#
# 工作原理：
#   GitHub = 餐厅
#   GitHub API = 餐厅的菜单（通过 HTTP 请求操作仓库）
#   GitHubClient = 服务员（帮你封装复杂的 HTTP 请求）
#
# 使用示例：
#   github = GitHubClient()
#   files = github.get_pr_files("owner", "repo", 1)  # 获取 PR 文件
#   github.create_pr_review(...)  # 发评论到 PR
#
# 文档：https://docs.github.com/en/rest
# ============================================================

class GitHubClient:
    """GitHub API 客户端

    封装 GitHub REST API 的 HTTP 请求，提供语义化的方法调用。
    无需记忆复杂 URL 和认证头，调用方法即可操作仓库。

    示例：
        github = GitHubClient()
        files = github.get_pr_files("owner", "repo", 1)
        github.create_pr_review(owner="owner", repo="repo", pr_number=1,
                               commit_id="abc", comments=[...])
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        """初始化客户端

        Args:
            token: GitHub Personal Access Token
        """
        from config.settings import settings
        self.token = token or settings.github_token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        # 设置 HTTP 客户端超时和重试
        # BUG FIX: 原代码没有设置超时，导致 GitHub API 响应慢时请求挂起
        # 添加 30 秒超时防止长时间等待
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.retry_count = 3

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """获取 PR 改动的文件列表

        Args:
            owner: 仓库拥有者
            repo: 仓库名
            pr_number: PR 编号

        Returns:
            文件列表，每个元素包含 filename, status, additions, deletions, patch
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        for attempt in range(self.retry_count):
            try:
                with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException:
                if attempt == self.retry_count - 1:
                    raise
                continue

    def get_pr_details(self, owner: str, repo: str, pr_number: int) -> dict:
        """获取 PR 详情

        Returns:
            PR 详细信息（标题、描述、作者等）
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        for attempt in range(self.retry_count):
            try:
                with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException:
                if attempt == self.retry_count - 1:
                    raise
                continue

    def create_review_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int,
    ) -> dict:
        """在 PR 上创建单行评论

        Args:
            owner: 仓库拥有者
            repo: 仓库名
            pr_number: PR 编号
            body: 评论内容
            commit_id: 提交 SHA
            path: 文件路径
            line: 行号

        Returns:
            创建的评论
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        payload = {
            "body": body,
            "commit_id": commit_id,
            "path": path,
            "line": line,
        }
        for attempt in range(self.retry_count):
            try:
                with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
                    response = client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException:
                if attempt == self.retry_count - 1:
                    raise
                continue

    def create_pr_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_id: str,
        comments: list[dict],
    ) -> dict:
        """创建 PR Review（多行评论）

        Args:
            owner: 仓库拥有者
            repo: 仓库名
            pr_number: PR 编号
            commit_id: 提交 SHA
            comments: 评论列表 [{"path": "...", "line": 1, "body": "..."}]

        Returns:
            创建的 review
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        payload = {
            "commit_id": commit_id,
            "event": "COMMENT",
            "comments": comments,
        }
        for attempt in range(self.retry_count):
            try:
                with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
                    response = client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException:
                if attempt == self.retry_count - 1:
                    raise
                continue