from unittest.mock import MagicMock, patch


@patch("src.agents.router_agent.ChatOpenAI")
def test_router_classifies_security_files(mock_chat_openai):
    """测试路由器识别安全文件"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.router_agent import RouterAgent

    mock_result = MagicMock()
    mock_result.content = '{"routes": {"auth.py": ["security"], "login.py": ["security", "bug"]}}'

    agent = RouterAgent()

    # Mock the chain's invoke
    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.route([
            {"filename": "auth.py", "contents": "SELECT * FROM users WHERE password = '" + "' OR '1'='1"},
            {"filename": "login.py", "contents": "subprocess.call(['ls', '-la'])"},
        ])
    assert "routes" in result
    assert "auth.py" in result["routes"]
    assert "security" in result["routes"]["auth.py"]


@patch("src.agents.router_agent.ChatOpenAI")
def test_router_classifies_bug_files(mock_chat_openai):
    """测试路由器识别 bug 文件"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.router_agent import RouterAgent

    mock_result = MagicMock()
    mock_result.content = '{"routes": {"calculator.py": ["bug"], "logic.py": ["bug"]}}'

    agent = RouterAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.route([
            {"filename": "calculator.py", "contents": "result = a / b"},
            {"filename": "logic.py", "contents": "if items[i] is None:"},
        ])
    assert "routes" in result
    assert "calculator.py" in result["routes"]
    assert "bug" in result["routes"]["calculator.py"]


@patch("src.agents.router_agent.ChatOpenAI")
def test_router_classifies_style_files(mock_chat_openai):
    """测试路由器识别 style 文件"""
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm

    from src.agents.router_agent import RouterAgent

    mock_result = MagicMock()
    mock_result.content = '{"routes": {"formatter.py": ["style"]}}'

    agent = RouterAgent()

    mock_chain = agent.prompt | agent.llm
    with patch.object(type(mock_chain), "invoke", return_value=mock_result):
        result = agent.route([
            {"filename": "formatter.py", "contents": "def foo():pass"},
        ])
    assert "routes" in result
    assert "formatter.py" in result["routes"]
    assert "style" in result["routes"]["formatter.py"]