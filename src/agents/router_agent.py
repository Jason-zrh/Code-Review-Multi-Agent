import json
import re
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings
from src.utils.token_counter import batch_by_tokens, estimate_tokens


class RouterAgent:
    """代码审查路由器 Agent

    Phase 2: 将文件路由到专门的审查 Agent
    - security: SQL/命令注入、文件操作、认证相关
    - bug: 逻辑、计算、空指针检查
    - style: 格式、命名、文档
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.1,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a code review router. Analyze each file and determine which review agents should process it.

Return a JSON object mapping filenames to their required review categories:
{{"routes": {{"filename.py": ["security", "bug", "style"], "another.py": ["bug"]}}}}

Categories:
- security: files with SQL, commands, file operations, auth
- bug: files with logic, calculations, null checks, loops
- style: files with formatting, naming, docstrings

Always include "security" and "bug" if file contains code, "style" is optional."""),
            ("human", "Files to route:\n{files_json}")
        ])

    def _prepare_file_content(self, content: str, max_tokens: int = 2000) -> str:
        """
        准备文件内容用于路由。

        如果文件太大，按行截断但保留开头和结尾（因为漏洞可能在任何位置）。
        保留前 70% 和后 30%。

        Args:
            content: 文件内容
            max_tokens: 最大 token 数

        Returns:
            处理后的内容
        """
        tokens = estimate_tokens(content)
        if tokens <= max_tokens:
            return content

        # 按比例截断
        lines = content.split('\n')
        total_lines = len(lines)

        # 保留前 70% 和后 30%
        keep_start = int(total_lines * 0.7)
        keep_end = total_lines

        if keep_start < total_lines:
            truncated = '\n'.join(lines[:keep_start]) + \
                       f"\n\n... ({total_lines - keep_start} more lines) ...\n\n" + \
                       '\n'.join(lines[keep_end - int(total_lines * 0.3):keep_end])
            return truncated

        return content[:int(max_tokens * 3.5)]  # 兜底：按 char 截断

    def route(self, files: list[dict]) -> dict:
        """将文件路由到适当的审查 Agent

        Args:
            files: 文件列表，每个包含 filename, contents

        Returns:
            路由结果 dict，格式: {"routes": {"filename": ["category", ...]}}
        """
        all_routes = {}

        # 按 token limit 分批处理
        batches = batch_by_tokens(files, token_limit=25000)
        print(f"[Router] Processing {len(files)} files in {len(batches)} batches")

        for batch_idx, batch in enumerate(batches):
            # 为每个文件准备合适的内容（不过度截断）
            files_json = "\n".join([
                f"{f['filename']}:\n{self._prepare_file_content(f.get('contents', ''), max_tokens=1500)}"
                for f in batch
            ])

            chain = self.prompt | self.llm
            result = chain.invoke({"files_json": files_json})

            content = result.content

            # 处理 MiniMax 的思考过程标签
            think_match = re.search(r'\s*', content, re.DOTALL)
            if think_match:
                content = content[think_match.end():]

            # 提取 JSON
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                batch_routes = json.loads(match.group())
                if "routes" in batch_routes:
                    all_routes.update(batch_routes["routes"])

        return {"routes": all_routes}