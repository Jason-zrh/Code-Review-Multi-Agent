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


@patch("src.agents.router_agent.RouterAgent")
@patch("src.agents.security_agent.SecurityAgent")
@patch("src.agents.bug_agent.BugAgent")
@patch("src.agents.style_agent.StyleAgent")
@patch("src.agents.aggregator_agent.AggregatorAgent")
def test_workflow_run(mock_agg, mock_style, mock_bug, mock_security, mock_router):
    """测试工作流执行"""
    # Mock router to return empty routes (defaults to all agents)
    mock_router_instance = MagicMock()
    mock_router_instance.route.return_value = {"routes": {}}
    mock_router.return_value = mock_router_instance

    # Mock security agent
    mock_security_instance = MagicMock()
    mock_security_instance.analyze.return_value = {"file": "test.py", "comments": []}
    mock_security.return_value = mock_security_instance

    # Mock bug agent
    mock_bug_instance = MagicMock()
    mock_bug_instance.analyze.return_value = {"file": "test.py", "comments": []}
    mock_bug.return_value = mock_bug_instance

    # Mock style agent
    mock_style_instance = MagicMock()
    mock_style_instance.analyze.return_value = {"file": "test.py", "comments": []}
    mock_style.return_value = mock_style_instance

    # Mock aggregator
    mock_agg_instance = MagicMock()
    mock_agg_instance.aggregate.return_value = {
        "comments": [],
        "overall_status": "success"
    }
    mock_agg.return_value = mock_agg_instance

    workflow = CodeReviewWorkflow()
    result = workflow.run(
        pr_id=123,
        repo_owner="owner",
        repo_name="repo",
        files=[],
    )
    assert result["overall_status"] == "success"


@patch("src.agents.router_agent.RouterAgent")
@patch("src.agents.security_agent.SecurityAgent")
@patch("src.agents.bug_agent.BugAgent")
@patch("src.agents.style_agent.StyleAgent")
@patch("src.agents.aggregator_agent.AggregatorAgent")
def test_workflow_with_pr_title(mock_agg, mock_style, mock_bug, mock_security, mock_router):
    """测试带 PR 标题的工作流"""
    # Mock router to return empty routes (defaults to all agents)
    mock_router_instance = MagicMock()
    mock_router_instance.route.return_value = {"routes": {}}
    mock_router.return_value = mock_router_instance

    # Mock all agents
    for mock in [mock_security, mock_bug, mock_style]:
        mock_instance = MagicMock()
        mock_instance.analyze.return_value = {"file": "test.py", "comments": []}
        mock.return_value = mock_instance

    mock_agg_instance = MagicMock()
    mock_agg_instance.aggregate.return_value = {
        "comments": [],
        "overall_status": "success"
    }
    mock_agg.return_value = mock_agg_instance

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


@patch("src.github.client.GitHubClient")
@patch("src.agents.router_agent.RouterAgent")
@patch("src.agents.security_agent.SecurityAgent")
@patch("src.agents.bug_agent.BugAgent")
@patch("src.agents.style_agent.StyleAgent")
@patch("src.agents.aggregator_agent.AggregatorAgent")
def test_workflow_posts_review(mock_agg, mock_style, mock_bug, mock_security, mock_router, mock_github):
    """测试工作流发布评论到 GitHub"""
    # Mock router to return routes for all agents
    mock_router_instance = MagicMock()
    mock_router_instance.route.return_value = {
        "routes": {"test.py": ["security", "bug", "style"]}
    }
    mock_router.return_value = mock_router_instance

    # Mock security agent
    mock_security_instance = MagicMock()
    mock_security_instance.analyze.return_value = {
        "file": "test.py",
        "comments": [{"line": 10, "severity": "high", "message": "Security issue"}]
    }
    mock_security.return_value = mock_security_instance

    # Mock bug agent
    mock_bug_instance = MagicMock()
    mock_bug_instance.analyze.return_value = {
        "file": "test.py",
        "comments": [{"line": 20, "severity": "medium", "message": "Bug issue"}]
    }
    mock_bug.return_value = mock_bug_instance

    # Mock style agent
    mock_style_instance = MagicMock()
    mock_style_instance.analyze.return_value = {"file": "test.py", "comments": []}
    mock_style.return_value = mock_style_instance

    # Mock aggregator
    mock_agg_instance = MagicMock()
    mock_agg_instance.aggregate.return_value = {
        "comments": [
            ReviewComment(
                file="test.py",
                line=10,
                severity="high",
                category="security",
                message="Security issue"
            )
        ],
        "overall_status": "success"
    }
    mock_agg.return_value = mock_agg_instance

    # Mock GitHub client
    mock_client = MagicMock()
    mock_github.return_value = mock_client

    workflow = CodeReviewWorkflow()
    result = workflow.run(
        pr_id=123,
        repo_owner="owner",
        repo_name="repo",
        files=[{"filename": "test.py", "contents": "code", "patch": "@@ -1,1 +1,2 @@\n+line1\n+line2"}],
    )

    # 验证评论被发布
    assert mock_client.create_pr_review.called


@patch("src.agents.router_agent.RouterAgent")
@patch("src.agents.security_agent.SecurityAgent")
@patch("src.agents.bug_agent.BugAgent")
@patch("src.agents.style_agent.StyleAgent")
@patch("src.agents.aggregator_agent.AggregatorAgent")
def test_workflow_routes_based_on_router(mock_agg, mock_style, mock_bug, mock_security, mock_router):
    """测试工作流根据路由结果选择 agents"""
    # Mock router to return only security and bug (no style)
    mock_router_instance = MagicMock()
    mock_router_instance.route.return_value = {
        "routes": {"test.py": ["security", "bug"]}
    }
    mock_router.return_value = mock_router_instance

    # Mock agents
    mock_security_instance = MagicMock()
    mock_security_instance.analyze.return_value = {"file": "test.py", "comments": []}
    mock_security.return_value = mock_security_instance

    mock_bug_instance = MagicMock()
    mock_bug_instance.analyze.return_value = {"file": "test.py", "comments": []}
    mock_bug.return_value = mock_bug_instance

    mock_style_instance = MagicMock()
    mock_style_instance.analyze.return_value = {"file": "test.py", "comments": []}
    mock_style.return_value = mock_style_instance

    mock_agg_instance = MagicMock()
    mock_agg_instance.aggregate.return_value = {
        "comments": [],
        "overall_status": "success"
    }
    mock_agg.return_value = mock_agg_instance

    workflow = CodeReviewWorkflow()
    result = workflow.run(
        pr_id=123,
        repo_owner="owner",
        repo_name="repo",
        files=[{"filename": "test.py", "contents": "code"}],
    )

    # Verify only security and bug agents were called, style was skipped
    assert mock_security_instance.analyze.called
    assert mock_bug_instance.analyze.called
    # Style should not be called based on router result
    assert mock_style_instance.analyze.call_count == 0
