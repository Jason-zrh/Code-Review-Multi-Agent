from pydantic import BaseModel
from typing import Optional


# ============================================================
# 数据模型层
# 作用：定义系统中流转的核心数据结构
# 特点：使用 Pydantic 做自动类型验证和 JSON 序列化
# ============================================================

class PullRequest(BaseModel):
    """Pull Request 模型

    存储 PR 的基本信息，用于在系统内部传递
    """

    pr_id: int
    repo_owner: str
    repo_name: str
    title: str
    description: str
    # author 为可选字段，如果 GitHub API 没返回则为空
    author: Optional[str] = None


class FileChange(BaseModel):
    """文件变更模型

    描述单个文件的改动（新增/修改/删除）
    """

    filename: str
    status: str  # "added" | "modified" | "removed"
    additions: int = 0  # 新增行数
    deletions: int = 0   # 删除行数
    patch: Optional[str] = None  # diff 补丁内容


class ReviewComment(BaseModel):
    """审查评论模型

    单条审查结果，对应 GitHub PR 评论
    """

    file: str                      # 文件路径
    line: Optional[int] = None     # 代码行号（可选，全局问题不指定）
    severity: str                   # 严重程度：info | warning | error | critical
    category: str                  # 问题分类：bug | security | style | performance
    message: str                   # 具体问题描述


class RouteResult(BaseModel):
    """路由结果模型

    Phase 2: 路由器分类文件并返回路由结果
    """
    routes: dict[str, list[str]]  # filename -> list of categories


class ReviewResult(BaseModel):
    """审查结果模型

    整个 PR 的审查汇总，包含多条评论
    """

    pr_id: int
    overall_status: str  # 整体状态：success | failed
    summary: Optional[str] = None  # 总结文本（可选）
    comments: list[ReviewComment] = []  # 问题列表
