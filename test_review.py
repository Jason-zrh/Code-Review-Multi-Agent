#!/usr/bin/env python3
"""
本地代码审查测试脚本

直接分析测试仓库的代码，无需 GitHub Webhook
"""
from src.coordinator.workflow import CodeReviewWorkflow


def main():
    # 读取测试文件
    test_repo = "/Users/renhezhang/Desktop/code-review-test"

    print("读取测试文件...")

    files = [
        {"filename": "auth.py", "contents": open(f"{test_repo}/auth.py").read()},
        {"filename": "utils.py", "contents": open(f"{test_repo}/utils.py").read()},
        {"filename": "main.py", "contents": open(f"{test_repo}/main.py").read()},
    ]

    # 运行审查
    print("触发 LLM 代码审查...\n")

    workflow = CodeReviewWorkflow()
    result = workflow.run(
        pr_id=1,
        repo_owner="Jason-zrh",
        repo_name="Code-review-test",
        files=files,
        pr_title="Test PR",
    )

    # 输出结果
    print("=" * 50)
    print("代码审查结果")
    print("=" * 50)
    print(f"\n发现问题: {len(result['review_comments'])} 个\n")

    for i, c in enumerate(result['review_comments'], 1):
        severity_icon = {
            "critical": "🔴",
            "error": "🟠",
            "warning": "🟡",
            "info": "🔵"
        }.get(c.severity, "⚪")

        print(f"{i}. {severity_icon} [{c.severity.upper()}] {c.file}:{c.line}")
        print(f"   类型: {c.category}")
        print(f"   问题: {c.message}\n")


if __name__ == "__main__":
    main()
