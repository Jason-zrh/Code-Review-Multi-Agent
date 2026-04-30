"""
Token 计数工具

提供基于字符数估算 tokens 的功能，以及按 token limit 分批的工具函数。
不需要调用 API，基于经验公式估算。
"""

from config.settings import settings

# 从 settings 读取配置（统一配置管理）
MAX_CONTEXT_TOKENS = settings.max_context_tokens
MAX_FILE_CHUNK_LINES = settings.max_file_chunk_lines
ENABLE_BATCHING = settings.enable_batching


def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量。

    经验公式：
    - 英文代码: chars / 3.5 ≈ tokens
    - 中文文本: chars / 2 ≈ tokens
    - 混合内容: chars / 4（保守估算）

    Args:
        text: 要估算的文本

    Returns:
        估算的 token 数量
    """
    if not text:
        return 0

    # 检测是否为纯英文（代码通常都是英文）
    has_chinese = any('一' <= c <= '鿿' for c in text)
    has_cjk = any('぀' <= c <= 'ヿ' for c in text)  # 日文

    if has_chinese or has_cjk:
        # 中文/日文：chars / 2
        return len(text) // 2
    else:
        # 英文/代码：chars / 3.5，但最少每个字符算 0.25 token
        return max(len(text) // 4, len(text) * 25 // 100)


def estimate_file_tokens(file_content: str, filename: str = "") -> int:
    """
    估算单个文件的 token 数量。

    对于已知文件类型，可以应用不同的估算系数。

    Args:
        file_content: 文件内容
        filename: 文件名（用于判断文件类型）

    Returns:
        估算的 token 数量
    """
    if not file_content:
        return 0

    # 不同文件类型有不同的估算系数
    code_extensions = {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rs', '.rb'}
    config_extensions = {'.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.xml'}
    markup_extensions = {'.html', '.css', '.scss', '.md', '.rst'}

    import os
    ext = os.path.splitext(filename)[1].lower()

    if ext in code_extensions:
        # 代码文件：chars / 3.5
        return estimate_tokens(file_content)
    elif ext in config_extensions:
        # 配置文件：chars / 4
        return len(file_content) // 4
    elif ext in markup_extensions:
        # 标记语言：chars / 4
        return len(file_content) // 4
    else:
        # 其他文件：保守估算 chars / 4
        return estimate_tokens(file_content)


def batch_by_tokens(
    items: list[dict],
    token_limit: int = None,
    get_content: callable = None,
    get_filename: callable = None
) -> list[list[dict]]:
    """
    将文件列表按 token 数量分批。

    Args:
        items: 文件列表，每个是 dict
        token_limit: 每批最大 token 数，默认使用 MAX_CONTEXT_TOKENS
        get_content: 从 item 中提取内容的函数，默认取 item.get("contents", "")
        get_filename: 从 item 中提取文件名的函数，默认取 item.get("filename", "")

    Returns:
        分批后的列表，每批是一个文件列表
    """
    if token_limit is None:
        token_limit = MAX_CONTEXT_TOKENS

    # 留 4K buffer
    token_limit = max(token_limit - 4000, 5000)

    if get_content is None:
        get_content = lambda item: item.get("contents", "")
    if get_filename is None:
        get_filename = lambda item: item.get("filename", "")

    batches = []
    current_batch = []
    current_tokens = 0

    for item in items:
        content = get_content(item)
        filename = get_filename(item)
        item_tokens = estimate_file_tokens(content, filename)

        if current_tokens + item_tokens > token_limit:
            if current_batch:
                batches.append(current_batch)
            current_batch = [item]
            current_tokens = item_tokens
        else:
            current_batch.append(item)
            current_tokens += item_tokens

    if current_batch:
        batches.append(current_batch)

    return batches


def check_within_limit(text: str, limit: int = None) -> bool:
    """
    检查文本是否在 token limit 内。

    Args:
        text: 要检查的文本
        limit: token 上限，默认使用 MAX_CONTEXT_TOKENS

    Returns:
        True if within limit, False otherwise
    """
    if limit is None:
        limit = MAX_CONTEXT_TOKENS
    return estimate_tokens(text) <= limit
