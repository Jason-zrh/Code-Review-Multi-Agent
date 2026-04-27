from typing import TypedDict, NotRequired, Annotated
from langgraph.types import Send
from langgraph.graph import StateGraph, END
from src.models.schemas import ReviewComment


# ============================================================
# 工作流层（LangGraph 状态机）
# 作用：定义 Multi-Agent 审查流程（Phase 2 并行架构）
# ============================================================

def _merge_agent_results(left: dict, right: dict) -> dict:
    """Reducer for merging agent_results from parallel nodes.

    Each node returns {"agent_results": {"agent_name": [...]}}.
    This reducer combines all agent results into a single dict.
    """
    result = {}
    # Process left
    if left:
        for key, value in left.items():
            if key == "agent_results" and isinstance(value, dict):
                for agent_name, agent_data in value.items():
                    if agent_name not in result:
                        result[agent_name] = agent_data
                    elif isinstance(agent_data, list):
                        result[agent_name] = result.get(agent_name, []) + agent_data
            else:
                result[key] = value
    # Process right
    if right:
        for key, value in right.items():
            if key == "agent_results" and isinstance(value, dict):
                for agent_name, agent_data in value.items():
                    if agent_name not in result:
                        result[agent_name] = agent_data
                    elif isinstance(agent_data, list):
                        result[agent_name] = result.get(agent_name, []) + agent_data
            else:
                result[key] = value
    return {"agent_results": result}


class ReviewState(TypedDict):
    """审查状态"""
    pr_id: int
    repo_owner: str
    repo_name: str
    files: list
    pr_title: NotRequired[str]
    pr_description: NotRequired[str]
    routes: NotRequired[dict]          # Router result: {"routes": {"filename": ["security", "bug", ...]}}
    agent_results: Annotated[NotRequired[dict], _merge_agent_results]  # Results from all agents
    review_comments: NotRequired[list]
    overall_status: NotRequired[str]


class CodeReviewWorkflow:
    """代码审查工作流 - Phase 2 并行多 Agent 架构"""

    def __init__(self):
        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        builder = StateGraph(ReviewState)

        # Add all nodes
        builder.add_node("route", self._node_route)
        builder.add_node("analyze_security", self._node_analyze_security)
        builder.add_node("analyze_bug", self._node_analyze_bug)
        builder.add_node("analyze_style", self._node_analyze_style)
        builder.add_node("aggregate", self._node_aggregate)
        builder.add_node("post_comments", self._node_post_comments)

        builder.set_entry_point("route")

        # Use conditional edges for fan-out from route node
        # _route_to_agents returns a list of Send objects for parallel execution
        builder.add_conditional_edges(
            "route",
            self._route_to_agents,
            ["analyze_security", "analyze_bug", "analyze_style"]
        )

        # All agents converge to aggregate
        builder.add_edge("analyze_security", "aggregate")
        builder.add_edge("analyze_bug", "aggregate")
        builder.add_edge("analyze_style", "aggregate")
        builder.add_edge("aggregate", "post_comments")
        builder.add_edge("post_comments", END)

        return builder

    def _route_to_agents(self, state: ReviewState) -> list[Send]:
        """Determine which agents to run based on router result

        Returns a list of Send objects for fan-out parallel execution.
        Each Send object specifies the target node and passes the state.
        """
        routes = state.get("routes", {})
        sends = []

        if not routes:
            # Default to all agents if no routes
            sends.append(Send("analyze_security", state))
            sends.append(Send("analyze_bug", state))
            sends.append(Send("analyze_style", state))
            return sends

        # Collect which agents to run based on routes
        run_security = False
        run_bug = False
        run_style = False

        for filename, categories in routes.items():
            if "security" in categories:
                run_security = True
            if "bug" in categories:
                run_bug = True
            if "style" in categories:
                run_style = True

        # Default to all agents if no specific routes matched
        if not run_security and not run_bug and not run_style:
            run_security = True
            run_bug = True
            run_style = True

        if run_security:
            sends.append(Send("analyze_security", state))
        if run_bug:
            sends.append(Send("analyze_bug", state))
        if run_style:
            sends.append(Send("analyze_style", state))

        return sends

    def _prepare_files(self, files: list) -> list:
        """Ensure files have contents field populated from patch"""
        for f in files:
            if "contents" not in f:
                f["contents"] = f.get("patch", "")
        return files

    def _node_route(self, state: ReviewState) -> dict:
        """Router node: classify files to appropriate agents"""
        from src.agents.router_agent import RouterAgent

        agent = RouterAgent()
        files = self._prepare_files(state.get("files", []))
        result = agent.route(files)

        # RouterAgent.route() returns {"routes": {"filename": ["category", ...]}}
        # We pass through the routes directly
        return result

    def _node_analyze_security(self, state: ReviewState) -> dict:
        """Security analysis node"""
        from src.agents.security_agent import SecurityAgent

        agent = SecurityAgent()
        files = self._prepare_files(state.get("files", []))
        results = []

        for f in files:
            result = agent.analyze(f["filename"], f.get("contents", ""))
            results.append(result)

        return {"agent_results": {"security": results}}

    def _node_analyze_bug(self, state: ReviewState) -> dict:
        """Bug detection node"""
        from src.agents.bug_agent import BugAgent

        agent = BugAgent()
        files = self._prepare_files(state.get("files", []))
        results = []

        for f in files:
            result = agent.analyze(f["filename"], f.get("contents", ""))
            results.append(result)

        return {"agent_results": {"bug": results}}

    def _node_analyze_style(self, state: ReviewState) -> dict:
        """Style analysis node"""
        from src.agents.style_agent import StyleAgent

        agent = StyleAgent()
        files = self._prepare_files(state.get("files", []))
        results = []

        for f in files:
            result = agent.analyze(f["filename"], f.get("contents", ""))
            results.append(result)

        return {"agent_results": {"style": results}}

    def _node_aggregate(self, state: ReviewState) -> dict:
        """Aggregate node: combine results from all agents"""
        from src.agents.aggregator_agent import AggregatorAgent

        agent_results = state.get("agent_results", {})
        if not agent_results:
            return {
                "review_comments": [],
                "overall_status": "success"
            }

        aggregator = AggregatorAgent()
        result = aggregator.aggregate(agent_results)

        return {
            "review_comments": [c.model_dump() if hasattr(c, "model_dump") else c for c in result.get("comments", [])],
            "overall_status": result.get("overall_status", "success")
        }

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

    def _node_post_comments(self, state: ReviewState) -> dict:
        """Post comments node: publish review comments to GitHub"""
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
