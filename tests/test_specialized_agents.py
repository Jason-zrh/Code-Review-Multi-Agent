from unittest.mock import MagicMock, patch


@patch("src.agents.security_agent.ChatOpenAI")
def test_security_agent_detects_sql_injection(mock_chat_openai):
    """Test security agent detects SQL injection"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.security_agent import SecurityAgent

    mock_result = MagicMock()
    mock_result.content = '```json\n{"file": "auth.py", "comments": [{"line": 1, "severity": "high", "message": "Potential SQL injection vulnerability"}]}\n```'

    agent = SecurityAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.analyze("auth.py", 'SELECT * FROM users WHERE password = "?" + user_input')

    assert "file" in result
    assert result["file"] == "auth.py"
    assert "comments" in result
    assert len(result["comments"]) > 0
    assert result["comments"][0]["severity"] == "high"


@patch("src.agents.security_agent.ChatOpenAI")
def test_security_agent_detects_hardcoded_secrets(mock_chat_openai):
    """Test security agent detects hardcoded secrets"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.security_agent import SecurityAgent

    mock_result = MagicMock()
    mock_result.content = '{"file": "config.py", "comments": [{"line": 1, "severity": "high", "message": "Hardcoded API key detected"}]}'

    agent = SecurityAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.analyze("config.py", 'API_KEY = "sk-1234567890abcdef"')

    assert "file" in result
    assert len(result["comments"]) > 0


@patch("src.agents.bug_agent.ChatOpenAI")
def test_bug_agent_detects_null_pointer(mock_chat_openai):
    """Test bug agent detects null pointer dereference"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.bug_agent import BugAgent

    mock_result = MagicMock()
    mock_result.content = '{"file": "parser.py", "comments": [{"line": 1, "severity": "medium", "message": "Potential null pointer dereference"}]}'

    agent = BugAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.analyze("parser.py", "value = data.get(key); result = value.field")

    assert "file" in result
    assert result["file"] == "parser.py"
    assert "comments" in result
    assert len(result["comments"]) > 0


@patch("src.agents.bug_agent.ChatOpenAI")
def test_bug_agent_detects_division_by_zero(mock_chat_openai):
    """Test bug agent detects division by zero"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.bug_agent import BugAgent

    mock_result = MagicMock()
    mock_result.content = '{"file": "calculator.py", "comments": [{"line": 1, "severity": "high", "message": "Potential division by zero"}]}'

    agent = BugAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.analyze("calculator.py", "result = a / b")

    assert "file" in result
    assert len(result["comments"]) > 0


@patch("src.agents.style_agent.ChatOpenAI")
def test_style_agent_detects_missing_docstrings(mock_chat_openai):
    """Test style agent detects missing docstrings"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.style_agent import StyleAgent

    mock_result = MagicMock()
    mock_result.content = '{"file": "utils.py", "comments": [{"line": 1, "severity": "low", "message": "Function is missing a docstring"}]}'

    agent = StyleAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.analyze("utils.py", "def calculate(): pass")

    assert "file" in result
    assert result["file"] == "utils.py"
    assert "comments" in result
    assert len(result["comments"]) > 0


@patch("src.agents.style_agent.ChatOpenAI")
def test_style_agent_detects_bad_naming(mock_chat_openai):
    """Test style agent detects bad naming"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.style_agent import StyleAgent

    mock_result = MagicMock()
    mock_result.content = '{"file": "processor.py", "comments": [{"line": 1, "severity": "low", "message": "Variable name x is not descriptive"}]}'

    agent = StyleAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.analyze("processor.py", "x = 1; y = x + 2")

    assert "file" in result
    assert len(result["comments"]) > 0


@patch("src.agents.security_agent.ChatOpenAI")
def test_security_agent_handles_invalid_json(mock_chat_openai):
    """Test security agent handles invalid JSON gracefully"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.security_agent import SecurityAgent

    mock_result = MagicMock()
    mock_result.content = "This is not JSON output"

    agent = SecurityAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.analyze("test.py", "code = request.data")

    assert "file" in result
    assert result["file"] == "test.py"
    assert "comments" in result
    assert result["comments"] == []


@patch("src.agents.bug_agent.ChatOpenAI")
def test_bug_agent_handles_invalid_json(mock_chat_openai):
    """Test bug agent handles invalid JSON gracefully"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.bug_agent import BugAgent

    mock_result = MagicMock()
    mock_result.content = "Not valid JSON"

    agent = BugAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.analyze("test.py", "result = items[i]")

    assert "file" in result
    assert result["file"] == "test.py"
    assert result["comments"] == []


@patch("src.agents.style_agent.ChatOpenAI")
def test_style_agent_handles_invalid_json(mock_chat_openai):
    """Test style agent handles invalid JSON gracefully"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.style_agent import StyleAgent

    mock_result = MagicMock()
    mock_result.content = "Invalid output"

    agent = StyleAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.analyze("test.py", "def f(): pass")

    assert "file" in result
    assert result["file"] == "test.py"
    assert result["comments"] == []
