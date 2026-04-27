import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings


class StyleAgent:
    """Code Style Agent

    Phase 2: Analyzes code for style and readability issues
    - Missing docstrings
    - Poor naming conventions
    - Unreachable code
    - Redundant code
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.1,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a code style expert reviewing code for readability and maintainability issues.

Analyze the code and identify style issues. Return a JSON object with this structure:
{{"file": "filename.py", "comments": [{{"line": 1, "severity": "high|medium|low", "message": "description of issue"}}]}}

Check for these style issues:
1. Missing docstrings - functions/classes without documentation
2. Bad naming - unclear, single-letter, or misleading variable/function names
3. Unreachable code - code after return/break/continue that can never execute
4. Redundant code - duplicate logic, unnecessary variables, dead code
5. Long functions - functions that are too long and should be refactored
6. Deep nesting - excessive nesting that hurts readability

Set severity based on impact:
- low: style preferences, not bugs (naming, docstrings)
- medium: maintainability concerns (redundancy, long functions)
- high: code quality issues (unreachable code, logic that looks buggy)

Focus on Python best practices. Be constructive with suggestions."""),
            ("human", "File: {filename}\n\nCode:\n{code}")
        ])

    def analyze(self, filename: str, code: str) -> dict:
        """Analyze code for style issues

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
