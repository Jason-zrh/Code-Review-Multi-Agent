from typing import TypedDict, NotRequired
from langgraph.graph import StateGraph, END
from src.models.schemas import ReviewComment


# ============================================================
# 工作流层（LangGraph 状态机）
# 作用：定义 Multi-Agent 审查流程
# 核心概念：
#   - State（状态）：整个流程共享的数据
#   - Node（节点）：处理步骤，相当于流水线上的工位
#   - Edge（边）：节点间的连接
# ============================================================

# ----------------------------------------------------------
# 状态定义
# 类似muduo的HttpConnection::MessageState，定义流程中的数据结构
# ----------------------------------------------------------
class ReviewState(TypedDict):
    """审查状态

    整个工作流中共享的数据结构
    每个节点都可以读取和修改这些数据
    """

    pr_id: int                     # PR 编号
    repo_owner: str                # 仓库拥有者
    repo_name: str                 # 仓库名
    files: list                    # 改动的文件列表
    review_comments: NotRequired[list[ReviewComment]]  # 审查结果
    overall_status: NotRequired[str]  # 整体状态


# ----------------------------------------------------------
# 工作流类
# ----------------------------------------------------------
class CodeReviewWorkflow:
    """代码审查工作流

    Phase 1：简单的三节点顺序流程
    Phase 2+：拆成 Coordinator + Bug/Security/Style Agents
    """

    def __init__(self):
        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """构建状态图

        LangGraph 的核心：定义有哪些节点，节点间怎么连接

        当前流程（Phase 1）：
            [start] -> [analyze] -> [finish] -> END
        """
        builder = StateGraph(ReviewState)

        # 添加处理节点
        builder.add_node("start", self._node_start)     # 开始
        builder.add_node("analyze", self._node_analyze) # 分析
        builder.add_node("finish", self._node_finish)   # 结束

        # 定义流向
        builder.set_entry_point("start")        # 入口节点
        builder.add_edge("start", "analyze")   # start -> analyze
        builder.add_edge("analyze", "finish")   # analyze -> finish
        builder.add_edge("finish", END)         # finish -> 结束

        return builder

    def _node_start(self, state: ReviewState) -> ReviewState:
        """开始节点

        初始化：什么都不做，直接传递状态
        """
        return state

    def _node_analyze(self, state: ReviewState) -> ReviewState:
        """分析节点

        Phase 1：空实现，后续接入 LLM 做代码分析
        """
        state["review_comments"] = []
        return state

    def _node_finish(self, state: ReviewState) -> ReviewState:
        """完成节点

        设置整体状态为成功
        """
        state["overall_status"] = "success"
        return state

    def run(
        self,
        pr_id: int,
        repo_owner: str,
        repo_name: str,
        files: list,
    ) -> dict:
        """运行工作流

        Args:
            pr_id: PR 编号
            repo_owner: 仓库拥有者
            repo_name: 仓库名
            files: 改动的文件列表

        Returns:
            最终状态字典
        """
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
