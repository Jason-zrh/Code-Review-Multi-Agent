import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.models.schemas import ReviewComment


class CodeReviewerAgent:
    """代码审查 Agent

    使用 LLM 分析代码，提供 Bug 检测、安全问题、风格建议
    Phase 1：单 Agent 混合分析
    Phase 2+：拆分为 Bug/Security/Style 多个 Agent
    """

    def __init__(self):
        """初始化 Agent 和 LLM"""
        from config.settings import settings

        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,  # 较低温度保证稳定性
        )

        # 分析单个文件的 prompt
        self.file_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的代码审查专家。
分析代码并找出以下问题：
1. Bug：空指针、数组越界、逻辑错误
2. 安全：注入漏洞、XSS、权限问题
3. 风格：命名规范、注释缺失

只报告真正的问题，不要鸡蛋里挑骨头。

返回 JSON 格式：
{{
    "file": "文件名",
    "comments": [
        {{
            "line": 行号或null,
            "severity": "info|warning|error|critical",
            "category": "bug|security|style",
            "message": "问题描述"
        }}
    ]
}}
如果没发现问题，comments 数组为空。"""),
            ("human", "文件：{filename}\n\n补丁：\n{patch}\n\n代码：\n{code}")
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

        # 解析 JSON 返回
        try:
            return json.loads(result.content)
        except json.JSONDecodeError:
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
