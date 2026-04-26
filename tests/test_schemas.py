from src.models.schemas import PullRequest, FileChange, ReviewResult, ReviewComment


def test_pull_request_model():
    """测试 PR 模型序列化"""
    pr = PullRequest(
        pr_id=123,
        repo_owner="test-owner",
        repo_name="test-repo",
        title="Fix login bug",
        description="Fixed null pointer exception",
    )
    data = pr.model_dump()
    assert data["pr_id"] == 123
    assert data["repo_owner"] == "test-owner"


def test_file_change_model():
    """测试文件变更模型"""
    change = FileChange(
        filename="src/auth.py",
        status="modified",
        additions=10,
        deletions=5,
        patch="@@ -1,5 +1,10 @@",
    )
    assert change.filename == "src/auth.py"
    assert change.status == "modified"


def test_review_result_model():
    """测试审查结果模型"""
    result = ReviewResult(
        pr_id=123,
        overall_status="success",
        comments=[
            ReviewComment(
                file="src/auth.py",
                line=42,
                severity="warning",
                category="bug",
                message="Potential null pointer",
            )
        ],
    )
    assert len(result.comments) == 1
    assert result.comments[0].severity == "warning"
