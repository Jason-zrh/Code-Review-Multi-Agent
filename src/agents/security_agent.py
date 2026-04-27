import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings


class SecurityAgent:
    """Security Review Agent

    Phase 2: Analyzes code for security vulnerabilities
    - SQL injection
    - Command injection
    - Path traversal
    - Cross-site scripting (XSS)
    - Hardcoded secrets
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.1,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a security expert reviewing code for vulnerabilities.

Analyze the code and identify security issues. Return a JSON object with this structure:
{{"file": "filename.py", "comments": [{{"line": 1, "severity": "high|medium|low", "message": "description of issue"}}]}}

Check for these vulnerability types:
1. SQL injection - unsanitized database queries with user input
2. Command injection - unsanitized system commands
3. Path traversal - unsanitized file paths
4. XSS - unsanitized output to HTML/web pages
5. Hardcoded secrets - API keys, passwords, tokens in code

Set severity based on impact:
- high: direct exploitation possible (SQL injection, command injection, secrets)
- medium: potential abuse (path traversal, XSS)
- low: informational (incomplete sanitization)

Only report actual vulnerabilities, not theoretical ones. Include line numbers when identifiable."""),
            ("human", "File: {filename}\n\nCode:\n{code}")
        ])

    def analyze(self, filename: str, code: str) -> dict:
        """Analyze code for security vulnerabilities

        Args:
            filename: Name of the file being reviewed
            code: Source code content

        Returns:
            Dict with file and comments array
        """
        chain = self.prompt | self.llm
        result = chain.invoke({"filename": filename, "code": code})
        return self._parse_json_result(result.content, filename)

    def _parse_json_result(self, content: str, filename: str) -> dict:
        """Parse JSON from LLM response"""
        try:
            # Remove any thinking tags from MiniMax
            content = re.sub(r'</think>\s*', '', content, flags=re.DOTALL)

            # Extract JSON object or array
            match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', content)
            if match:
                return json.loads(match.group())

            return {"file": filename, "comments": []}
        except json.JSONDecodeError:
            return {"file": filename, "comments": []}
