"""Aggregator Agent - Combines results from multiple specialized agents"""
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.models.schemas import ReviewComment
from config.settings import settings


class AggregatorAgent:
    """Combines results from multiple specialized agents into a single review."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.1,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the lead of a code review team. Combine results from multiple specialized agents.\n\nGenerate a summary JSON with fields: overall_status (success/partial/failed), summary (string), total_issues (int), critical_issues (int), by_category (dict).\n\nStatus values: success=all reviewed, partial=something failed, failed=review failed"),
            ("human", "Agent results:\n{results_json}")
        ])

    def _deduplicate_comments(self, comments: list[ReviewComment]) -> list[ReviewComment]:
        """
        去重评论。

        同一文件同一行只保留一条评论。
        如果有多条评论来自不同 category，合并它们。
        如果 severity 不同，保留最严重的。

        Args:
            comments: 评论列表

        Returns:
            去重后的评论列表
        """
        # 按 (file, line) 分组
        from collections import defaultdict
        seen = defaultdict(list)

        for comment in comments:
            key = (comment.file, comment.line)
            seen[key].append(comment)

        result = []
        for key, group in seen.items():
            file_path, line = key

            # 按 severity 排序，critical > error > warning > info
            severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
            sorted_group = sorted(
                group,
                key=lambda c: severity_order.get(c.severity, 99)
            )

            # 保留最严重的那条
            best = sorted_group[0]

            # 如果有多个 category，合并它们
            categories = list(set(c.category for c in sorted_group))
            if len(categories) > 1:
                best.category = "+".join(sorted(categories))

            # 合并消息（如果不同）
            messages = list(set(c.message for c in sorted_group))
            if len(messages) > 1:
                best.message = " | ".join(messages)

            result.append(best)

        return result

    def aggregate(self, agent_results: dict[str, list]) -> dict:
        """Combine results from all agents with deduplication."""
        all_comments = []

        for category, results in agent_results.items():
            for result in results:
                for comment in result.get("comments", []):
                    all_comments.append(ReviewComment(
                        file=result.get("file", ""),
                        line=comment.get("line"),
                        severity=comment.get("severity", "info"),
                        category=category,
                        message=comment.get("message", ""),
                    ))

        # 去重
        unique_comments = self._deduplicate_comments(all_comments)
        print(f"[Aggregator] {len(all_comments)} comments -> {len(unique_comments)} after deduplication")

        # Generate summary using LLM
        # 只对去重后的结果生成摘要
        results_json = json.dumps(agent_results, ensure_ascii=False)
        chain = self.prompt | self.llm
        summary_result = chain.invoke({"results_json": results_json})

        try:
            summary_data = json.loads(summary_result.content)
        except json.JSONDecodeError:
            summary_data = {
                "overall_status": "success",
                "summary": "Review complete",
                "total_issues": len(unique_comments)
            }

        return {
            "overall_status": summary_data.get("overall_status", "success"),
            "summary": summary_data.get("summary", ""),
            "comments": unique_comments,
        }