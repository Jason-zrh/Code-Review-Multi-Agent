import httpx
from typing import Optional


class GitHubClient:
    """GitHub API 客户端

    用于获取 PR 信息和评论 PR
    文档：https://docs.github.com/en/rest
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
        with httpx.Client(headers=self.headers) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()

    def get_pr_details(self, owner: str, repo: str, pr_number: int) -> dict:
        """获取 PR 详情

        Returns:
            PR 详细信息（标题、描述、作者等）
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        with httpx.Client(headers=self.headers) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()

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
        with httpx.Client(headers=self.headers) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

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
        with httpx.Client(headers=self.headers) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()