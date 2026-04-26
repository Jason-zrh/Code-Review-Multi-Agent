from unittest.mock import patch, MagicMock
from src.coordinator.workflow import CodeReviewWorkflow, ReviewState
from src.models.schemas import ReviewComment


def test_review_state_initialization():
    """测试状态初始化"""
    state = ReviewState(
        pr_id=123,
        repo_owner="owner",
        repo_name="repo",
        files=[],
    )
    assert state["pr_id"] == 123


def test_workflow_initialization():
    """测试工作流初始化"""
    workflow = CodeReviewWorkflow()
    assert workflow.graph is not None
    assert workflow.app is not None


@patch("src.agents.code_reviewer.ChatOpenAI")
@patch("src.agents.code_reviewer.CodeReviewerAgent")
def test_workflow_run(mock_agent_class, mock_llm):
    """测试工作流执行"""
    mock_agent = MagicMock()
    mock_agent.analyze_pr.return_value = {
        "comments": [],
        "overall_status": "success",
    }
    mock_agent_class.return_value = mock_agent

    workflow = CodeReviewWorkflow()
    result = workflow.run(
        pr_id=123,
        repo_owner="owner",
        repo_name="repo",
        files=[],
    )
    assert result["overall_status"] == "success"


@patch("src.agents.code_reviewer.ChatOpenAI")
@patch("src.agents.code_reviewer.CodeReviewerAgent")
def test_workflow_with_pr_title(mock_agent_class, mock_llm):
    """测试带 PR 标题的工作流"""
    mock_agent = MagicMock()
    mock_agent.analyze_pr.return_value = {
        "comments": [],
        "overall_status": "success",
    }
    mock_agent_class.return_value = mock_agent

    workflow = CodeReviewWorkflow()
    result = workflow.run(
        pr_id=123,
        repo_owner="owner",
        repo_name="repo",
        files=[],
        pr_title="Test PR",
        pr_description="Test description",
    )
    assert "overall_status" in result
