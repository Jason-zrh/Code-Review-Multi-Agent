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

    def aggregate(self, agent_results: dict[str, list]) -> dict:
        """Combine results from all agents."""
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

        # Generate summary using LLM
        results_json = json.dumps(agent_results, ensure_ascii=False)
        chain = self.prompt | self.llm
        summary_result = chain.invoke({"results_json": results_json})

        try:
            summary_data = json.loads(summary_result.content)
        except json.JSONDecodeError:
            summary_data = {
                "overall_status": "success",
                "summary": "Review complete",
                "total_issues": len(all_comments)
            }

        return {
            "overall_status": summary_data.get("overall_status", "success"),
            "summary": summary_data.get("summary", ""),
            "comments": all_comments,
        }