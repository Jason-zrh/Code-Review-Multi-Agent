from src.coordinator.workflow import CodeReviewWorkflow, ReviewState


def test_review_state_initialization():
    """测试状态初始化"""
    state = ReviewState(
        pr_id=123,
        repo_owner="owner",
        repo_name="repo",
        files=[],
        review_comments=[],
    )
    assert state["pr_id"] == 123
    assert state["review_comments"] == []


def test_workflow_initialization():
    """测试工作流初始化"""
    workflow = CodeReviewWorkflow()
    assert workflow.graph is not None
    assert workflow.app is not None


def test_workflow_run():
    """测试工作流执行"""
    workflow = CodeReviewWorkflow()
    result = workflow.run(
        pr_id=123,
        repo_owner="owner",
        repo_name="repo",
        files=[],
    )
    assert result["overall_status"] == "success"
