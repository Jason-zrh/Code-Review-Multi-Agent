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

    def _node_finish(self, state: ReviewState) -> ReviewState:
        """完成节点：发布评论到 GitHub"""
        from src.github.client import GitHubClient

        try:
            github = GitHubClient()
            comments = state.get("review_comments", [])

            if comments:
                # 获取 PR 详情以获取正确的 commit SHA
                pr_details = github.get_pr_details(
                    owner=state["repo_owner"],
                    repo=state["repo_name"],
                    pr_number=state["pr_id"],
                )
                commit_id = pr_details.get("head", {}).get("sha", "HEAD")

                # 转换评论格式为 GitHub API 格式（支持字典和 ReviewComment 对象）
                review_comments = []
                for c in comments:
                    if isinstance(c, dict):
                        review_comments.append({
                            "path": c.get("file", ""),
                            "line": c.get("line") or 1,
                            "body": f"[{c.get('category', '').upper()}] {c.get('message', '')}",
                        })
                    else:
                        review_comments.append({
                            "path": c.file,
                            "line": c.line or 1,
                            "body": f"[{c.category.upper()}] {c.message}",
                        })

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
