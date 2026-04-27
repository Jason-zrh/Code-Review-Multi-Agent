import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings


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

    def route(self, files: list[dict]) -> dict:
        """将文件路由到适当的审查 Agent

        Args:
            files: 文件列表，每个包含 filename, contents

        Returns:
            路由结果 dict，格式: {"routes": {"filename": ["category", ...]}}
        """
        files_json = "\n".join([f"{f['filename']}: {f['contents'][:200]}" for f in files])
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
            return json.loads(match.group())
        return {"routes": {}}