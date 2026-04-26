import json
import re
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.models.schemas import ReviewComment


class CodeReviewerAgent:
    """代码审查 Agent

    使用 LLM 分析代码，提供 Bug 检测、安全问题、风格建议
    Phase 1: 单 Agent 混合分析
    Phase 2+: 拆分为 Bug/Security/Style 多个 Agent
    """

    def __init__(self):
        """初始化 Agent 和 LLM"""
        from config.settings import settings

        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.3,  # 较低保证稳定性
        )

        # 分析单个文件的 prompt
        self.file_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert code reviewer. Analyze Python code and identify issues.

Focus on finding REAL bugs only:
1. SECURITY: SQL injection, XSS, path traversal, command injection, hardcoded secrets
2. BUGS: null pointer (None), index out of bounds, logic errors, unhandled exceptions, memory leaks
3. STYLE: missing docstrings, bad naming, unreachable code

IMPORTANT RULES:
- Find at least one issue per file if code exists
- Report issues that would cause runtime errors or security vulnerabilities

JSON format (pure JSON, no markdown):
{{"file": "FILENAME", "comments": [{{"line": 1, "severity": "LEVEL", "category": "TYPE", "message": "DESCRIPTION"}}]}}
Use severity: critical|error|warning|info
Use category: security|bug|style
Empty comments array only if code is clean."""),
            ("human", "File: {filename}\n\nCode:\n{code}")
        ])

        # 分析 PR 的 prompt
        self.pr_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是代码审查团队的负责人。
根据多个文件的审查结果，生成总结报告。

返回 JSON 格式：
{{
    "overall_status": "success|partial|failed",
    "summary": "总结文本",
    "total_issues": 问题总数
}}"""),
            ("human", "PR 标题：{pr_title}\nPR 描述：{pr_description}\n\n文件分析结果：\n{file_results}")
        ])

    def analyze_file(self, filename: str, code: str, patch: Optional[str] = None) -> dict:
        """分析单个文件

        Args:
            filename: 文件名
            code: 文件内容
            patch: diff 补丁

        Returns:
            分析结果字典
        """
        chain = self.file_prompt | self.llm
        result = chain.invoke({
            "filename": filename,
            "code": code,
            "patch": patch or "无",
        })

        # 解析 JSON 返回（处理 MiniMax 的思考过程标签）
        try:
            content = result.content

            # MiniMax 返回格式：<think> ...</think> {...json...}
            # 先去掉思考过程部分，只保留 JSON
            think_match = re.search(r'</think>\s*', content, re.DOTALL)
            if think_match:
                content = content[think_match.end():]

            # 查找 JSON 对象或数组
            json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', content)
            if json_match:
                content = json_match.group()
                return json.loads(content)
            return {"file": filename, "comments": []}
        except (json.JSONDecodeError, re.error):
            return {"file": filename, "comments": []}

    def analyze_pr(
        self,
        files: list[dict],
        pr_title: str = "",
        pr_description: str = "",
    ) -> dict:
        """分析整个 PR

        Args:
            files: 文件列表，每个包含 filename, contents, patch
            pr_title: PR 标题
            pr_description: PR 描述

        Returns:
            审查结果
        """
        file_results = []

        for f in files:
            result = self.analyze_file(
                filename=f.get("filename", ""),
                code=f.get("contents", ""),
                patch=f.get("patch"),
            )
            file_results.append(result)

        # 生成汇总
        chain = self.pr_prompt | self.llm
        summary = chain.invoke({
            "pr_title": pr_title,
            "pr_description": pr_description,
            "file_results": json.dumps(file_results, ensure_ascii=False),
        })

        try:
            summary_data = json.loads(summary.content)
        except json.JSONDecodeError:
            summary_data = {"overall_status": "partial", "summary": "分析完成", "total_issues": 0}

        # 合并所有评论
        all_comments = []
        for fr in file_results:
            for c in fr.get("comments", []):
                all_comments.append(
                    ReviewComment(
                        file=fr.get("file", ""),
                        line=c.get("line"),
                        severity=c.get("severity", "info"),
                        category=c.get("category", "style"),
                        message=c.get("message", ""),
                    )
                )

        return {
            "overall_status": summary_data.get("overall_status", "partial"),
            "summary": summary_data.get("summary", ""),
            "comments": all_comments,
        }
