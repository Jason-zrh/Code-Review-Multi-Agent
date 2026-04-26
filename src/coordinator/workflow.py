from typing import TypedDict, NotRequired, Literal
from langgraph.graph import StateGraph, END
from src.models.schemas import ReviewComment


class ReviewState(TypedDict):
    """审查状态"""

    pr_id: int
    repo_owner: str
    repo_name: str
    files: list
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

        # 添加入口节点
        builder.add_node("start", self._node_start)
        builder.add_node("analyze", self._node_analyze)
        builder.add_node("finish", self._node_finish)

        builder.set_entry_point("start")
        builder.add_edge("start", "analyze")
        builder.add_edge("analyze", "finish")
        builder.add_edge("finish", END)

        return builder

    def _node_start(self, state: ReviewState) -> ReviewState:
        """开始节点"""
        return state

    def _node_analyze(self, state: ReviewState) -> ReviewState:
        """分析节点（Phase 1 单 Agent）"""
        state["review_comments"] = []
        return state

    def _node_finish(self, state: ReviewState) -> ReviewState:
        """完成节点"""
        state["overall_status"] = "success"
        return state

    def run(
        self,
        pr_id: int,
        repo_owner: str,
        repo_name: str,
        files: list,
    ) -> dict:
        """运行工作流"""
        initial_state = ReviewState(
            pr_id=pr_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            files=files,
            review_comments=[],
            overall_status="pending",
        )
        result = self.app.invoke(initial_state)
        return result
