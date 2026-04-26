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
