import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings


class BugAgent:
    """Bug Detection Agent

    Phase 2: Analyzes code for potential bugs and errors
    - Null pointer dereferences
    - Index out of bounds
    - Division by zero
    - Logic errors
    - Resource leaks
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.1,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a bug detection expert reviewing code for potential issues.

Analyze the code and identify bugs. Return a JSON object with this structure:
{{"file": "filename.py", "comments": [{{"line": 1, "severity": "high|medium|low", "message": "description of issue"}}]}}

Check for these bug types:
1. Null pointer dereference - accessing members/calls on potentially null objects
2. Index out of bounds - array/list access without bounds checking
3. Division by zero - division operations without zero checks
4. Logic errors - incorrect conditional logic, off-by-one errors
5. Resource leaks - unclosed files, connections, or streams
6. Race conditions - concurrent access without proper synchronization

Set severity based on crash likelihood and impact:
- high: will cause runtime errors (null deref, div by zero, OOB)
- medium: may cause incorrect behavior (logic errors, race conditions)
- low: minor issues or code smell (resource leaks, style)

Only report actual bugs, not code style preferences."""),
            ("human", "File: {filename}\n\nCode:\n{code}")
        ])

    def analyze(self, filename: str, code: str) -> dict:
        """Analyze code for bugs

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
