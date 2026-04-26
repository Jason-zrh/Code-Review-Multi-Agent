from typing import TypedDict, NotRequired
from langgraph.graph import StateGraph, END
from src.models.schemas import ReviewComment


# ============================================================
# 工作流层（LangGraph 状态机）
# 作用：定义 Multi-Agent 审查流程
# ============================================================

class ReviewState(TypedDict):
    """审查状态"""
    pr_id: int
    repo_owner: str
    repo_name: str
    files: list
    pr_title: NotRequired[str]
    pr_description: NotRequired[str]
    review_comments: NotRequired[list[ReviewComment]]
    overall_status: NotRequired[str]


class CodeReviewWorkflow:
    """代码审查工作流"""

    def __init__(self):
        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        builder = StateGraph(ReviewState)

        builder.add_node("start", self._node_start)
        builder.add_node("analyze", self._node_analyze)
        builder.add_node("finish", self._node_finish)

        builder.set_entry_point("start")
        builder.add_edge("start", "analyze")
        builder.add_edge("analyze", "finish")
        builder.add_edge("finish", END)

        return builder

    def _node_start(self, state: ReviewState) -> ReviewState:
        """开始节点：什么都不做"""
        return state

    def _node_analyze(self, state: ReviewState) -> ReviewState:
        """分析节点：调用 LLM 分析代码"""
        from src.agents.code_reviewer import CodeReviewerAgent

        agent = CodeReviewerAgent()
        files = state.get("files", [])

        # 如果没有 contents，从 patch 构建
        for f in files:
            if "contents" not in f:
                f["contents"] = f.get("patch", "")

        result = agent.analyze_pr(
            files=files,
            pr_title=state.get("pr_title", ""),
            pr_description=state.get("pr_description", ""),
        )

        state["review_comments"] = result.get("comments", [])
        state["overall_status"] = result.get("overall_status", "success")
        return state

    def _get_file_info(self, files: list) -> dict:
        """从 patch 中提取每个文件的信息，用于验证评论行号和 patch 有效性

        GitHub PR Review API 对行号有严格限制：
        1. 行号必须指向 patch 中实际存在的行
        2. 空文件或没有有效 patch 的文件无法发表评论
        3. LLM 生成的行号可能超出文件实际范围，需要验证
        """
        file_info = {}
        for f in files:
            filename = f.get("filename", "")
            patch = f.get("patch", "")
            if patch and filename:
                # 解析 patch 的 hunk header 获取行数信息
                # 格式: @@ -start,count +start,count @@
                # 例如: @@ -1,33 +1,37 @@ 表示原文件 33 行，新文件 37 行
                import re
                match = re.search(r'@@ -\d+,\d+ \+\d+,(\d+) @@', patch)
                if match:
                    file_info[filename] = {
                        "line_count": int(match.group(1)),
                        "has_patch": True
                    }
                else:
                    # 兜底：统计 patch 中的 + 行数
                    plus_lines = [l for l in patch.splitlines() if l.startswith('+') and not l.startswith('+++')]
                    if plus_lines:
                        file_info[filename] = {
                            "line_count": len(plus_lines),
                            "has_patch": True
                        }
                    else:
                        file_info[filename] = {"line_count": 0, "has_patch": False}
            elif filename:
                # 没有 patch 的文件，跳过
                file_info[filename] = {"line_count": 0, "has_patch": False}
        return file_info

    def _node_finish(self, state: ReviewState) -> ReviewState:
        """完成节点：发布评论到 GitHub"""
        from src.github.client import GitHubClient

        try:
            github = GitHubClient()
            comments = state.get("review_comments", [])

            if comments:
                # BUG FIX: 不能使用 "HEAD" 字符串作为 commit_id
                # GitHub PR Review API 要求提供有效的 40 位 SHA-1 提交哈希
                # "HEAD" 不是有效的 SHA，会导致 422 Unprocessable Entity 错误
                # 必须从 PR 详情中获取实际的 commit SHA
                pr_details = github.get_pr_details(
                    owner=state["repo_owner"],
                    repo=state["repo_name"],
                    pr_number=state["pr_id"],
                )
                commit_id = pr_details.get("head", {}).get("sha", "HEAD")

                # 构建文件信息映射，用于验证行号和patch有效性
                file_info = self._get_file_info(state.get("files", []))

                # 转换评论格式为 GitHub API 格式（支持字典和 ReviewComment 对象）
                review_comments = []
                skipped = 0
                for c in comments:
                    if isinstance(c, dict):
                        path = c.get("file", "")
                        line = c.get("line") or 1
                    else:
                        path = c.file
                        line = c.line or 1

                    # BUG FIX: 跳过没有有效 patch 的文件的评论
                    # GitHub PR Review API 无法在空文件或纯文本文件上发表评论
                    # 这些文件的 patch 为空或无效（如 .txt 文件）
                    # 会导致 "Line could not be resolved" 的 422 错误
                    info = file_info.get(path, {"has_patch": False, "line_count": 0})
                    if not info["has_patch"] or info["line_count"] == 0:
                        skipped += 1
                        continue

                    # 验证行号有效性：LLM 生成的行号可能超出文件实际范围
                    # 如果 LLM 报告的 line 号大于文件的总行数，会导致 422 错误
                    # 需要将行号限制在文件实际行数范围内
                    max_line = info["line_count"]
                    if line > max_line:
                        line = max_line

                    if isinstance(c, dict):
                        review_comments.append({
                            "path": path,
                            "line": line,
                            "body": f"[{c.get('category', '').upper()}] {c.get('message', '')}",
                        })
                    else:
                        review_comments.append({
                            "path": path,
                            "line": line,
                            "body": f"[{c.category.upper()}] {c.message}",
                        })

                if skipped > 0:
                    print(f"Skipped {skipped} comments on files without valid diff")

                if review_comments:
                    print(f"Posting {len(review_comments)} comments to PR #{state['pr_id']} with commit {commit_id}")
                    github.create_pr_review(
                        owner=state["repo_owner"],
                        repo=state["repo_name"],
                        pr_number=state["pr_id"],
                        commit_id=commit_id,
                        comments=review_comments,
                    )
                    print(f"Successfully posted comments to PR")
        except Exception as e:
            print(f"Error posting comments: {e}")
            pass  # 评论失败不影响整体流程

        if not state.get("overall_status"):
            state["overall_status"] = "success"
        return state

    def run(
        self,
        pr_id: int,
        repo_owner: str,
        repo_name: str,
        files: list,
        pr_title: str = "",
        pr_description: str = "",
    ) -> dict:
        """运行工作流"""
        initial_state = ReviewState(
            pr_id=pr_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            files=files,
            pr_title=pr_title,
            pr_description=pr_description,
            review_comments=[],
            overall_status="pending",
        )
        result = self.app.invoke(initial_state)
        return result
