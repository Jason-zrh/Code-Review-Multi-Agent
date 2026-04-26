from unittest.mock import MagicMock, patch
from src.agents.code_reviewer import CodeReviewerAgent


@patch("src.agents.code_reviewer.ChatOpenAI")
def test_code_reviewer_initialization(mock_chat_openai):
    """测试 Agent 初始化"""
    mock_chat_openai.return_value = MagicMock()
    agent = CodeReviewerAgent()
    assert agent.llm is not None


@patch("src.agents.code_reviewer.ChatOpenAI")
def test_analyze_file_method_exists(mock_chat_openai):
    """测试方法存在"""
    mock_chat_openai.return_value = MagicMock()
    agent = CodeReviewerAgent()
    assert hasattr(agent, "analyze_file")
    assert hasattr(agent, "analyze_pr")


@patch("src.agents.code_reviewer.ChatOpenAI")
def test_analyze_file_returns_dict(mock_chat_openai):
    """测试 analyze_file 返回字典结构"""
    mock_chat_openai.return_value = MagicMock()
    agent = CodeReviewerAgent()

    mock_invoke_result = MagicMock()
    mock_invoke_result.content = '{"file": "test.py", "comments": []}'

    mock_chain = agent.file_prompt | agent.llm

    with patch.object(type(mock_chain), "invoke", return_value=mock_invoke_result):
        result = agent.analyze_file(
            filename="test.py",
            code="def hello(): pass",
            patch="@@ -1,3 +1,3 @@"
        )
    assert "file" in result
    assert "comments" in result
