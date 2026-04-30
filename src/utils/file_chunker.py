"""
文件分块工具

将大型文件按逻辑边界（class/function）或行数分块，
使每个分块可以在 LLM context limit 内处理。
"""

import re
import os
from typing import TypedDict
from config.settings import settings

MAX_CONTEXT_TOKENS = settings.max_context_tokens
MAX_FILE_CHUNK_LINES = settings.max_file_chunk_lines


class FileChunk(TypedDict):
    """单个文件分块"""
    name: str           # 分块名称（通常是 class/function 名）
    content: str        # 分块内容
    line_start: int     # 在原文件中的起始行号（1-based）
    line_end: int       # 在原文件中的结束行号（1-based）


def chunk_by_class(content: str, max_chunk_tokens: int = None) -> list[FileChunk]:
    """
    按 class/function 分块，保持逻辑边界。

    策略：
    1. 找到所有顶级定义（class 或 def，不在其他函数内）
    2. 每个定义作为一个分块
    3. 如果单个分块仍超过 max_chunk_tokens，进一步按行拆分

    Args:
        content: 文件内容
        max_chunk_tokens: 每个分块的最大 token 数，默认 10000

    Returns:
        分块列表
    """
    if max_chunk_tokens is None:
        max_chunk_tokens = MAX_CONTEXT_TOKENS // 3  # 单个分块不超过 1/3 context

    lines = content.split('\n')

    # 找所有顶级定义
    # 匹配 class Foo: 或 def foo(): 或 async def foo():
    pattern = r'^(class\s+\w+|def\s+\w+|async\s+def\s+\w+)'

    top_level_starts = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and re.match(pattern, stripped):
            top_level_starts.append(i)

    # 如果没找到任何定义，按行数分块
    if not top_level_starts:
        return chunk_by_lines(content, max_chunk_tokens=max_chunk_tokens)

    # 构建分块
    chunks = []
    for i, start in enumerate(top_level_starts):
        end = top_level_starts[i + 1] if i + 1 < len(top_level_starts) else len(lines)
        chunk_lines = lines[start:end]
        chunk_content = '\n'.join(chunk_lines)
        chunk_tokens = estimate_tokens(chunk_content)

        # 如果单个分块太大，按行数进一步拆分
        if chunk_tokens > max_chunk_tokens:
            sub_chunks = chunk_by_lines(chunk_content, max_chunk_tokens)
            # 调整行号
            for j, sub in enumerate(sub_chunks):
                sub_chunks[j]['line_start'] = start + 1 + sub['line_start']
                sub_chunks[j]['line_end'] = start + sub['line_end']
                sub_chunks[j]['name'] = f"{sub['name']}_part{j + 1}"
            chunks.extend(sub_chunks)
        else:
            # 提取定义名称
            match = re.match(pattern, chunk_lines[0].strip())
            name = match.group(1) if match else f"chunk_{start + 1}"

            chunks.append(FileChunk(
                name=name,
                content=chunk_content,
                line_start=start + 1,  # 1-based
                line_end=end
            ))

    return chunks


def chunk_by_lines(content: str, max_chunk_lines: int = None, max_chunk_tokens: int = None) -> list[FileChunk]:
    """
    按行数分块，作为兜底策略。

    当无法按逻辑结构分块时使用。

    Args:
        content: 文件内容
        max_chunk_lines: 每块最大行数，默认使用 MAX_FILE_CHUNK_LINES
        max_chunk_tokens: 每块最大 token 数，默认使用 MAX_CONTEXT_TOKENS // 3

    Returns:
        分块列表
    """
    if max_chunk_lines is None:
        max_chunk_lines = MAX_FILE_CHUNK_LINES
    if max_chunk_tokens is None:
        max_chunk_tokens = MAX_CONTEXT_TOKENS // 3

    lines = content.split('\n')
    total_lines = len(lines)

    if total_lines <= max_chunk_lines:
        return [FileChunk(
            name="full_file",
            content=content,
            line_start=1,
            line_end=total_lines
        )]

    chunks = []
    for i in range(0, total_lines, max_chunk_lines):
        chunk_lines = lines[i:i + max_chunk_lines]
        chunk_content = '\n'.join(chunk_lines)
        chunk_tokens = estimate_tokens(chunk_content)

        # 如果 token 数仍然超标，进一步拆分
        if chunk_tokens > max_chunk_tokens:
            # 递归减少行数
            smaller_chunks = chunk_by_lines(content[i * max_chunk_lines:], max_chunk_lines // 2, max_chunk_tokens)
            for j, sub in enumerate(smaller_chunks):
                smaller_chunks[j]['line_start'] = i + 1 + sub['line_start']
                smaller_chunks[j]['line_end'] = i + sub['line_end']
            chunks.extend(smaller_chunks)
        else:
            chunks.append(FileChunk(
                name=f"lines_{i + 1}_{i + len(chunk_lines)}",
                content=chunk_content,
                line_start=i + 1,  # 1-based
                line_end=i + len(chunk_lines)
            ))

    return chunks


def chunk_large_file(content: str, filename: str = "", max_chunk_tokens: int = None) -> list[FileChunk]:
    """
    智能分块主函数。

    自动选择最佳分块策略：
    1. 小文件（< 2000 行）：不拆分
    2. 大文件有明确结构：按 class/function 分块
    3. 大文件无明确结构：按行数分块

    Args:
        content: 文件内容
        filename: 文件名（用于判断文件类型和结构）
        max_chunk_tokens: 每个分块的最大 token 数

    Returns:
        分块列表
    """
    lines = content.split('\n')
    total_lines = len(lines)
    total_tokens = estimate_tokens(content, filename)

    if total_tokens is None:
        total_tokens = estimate_tokens(content)

    if total_tokens is None:
        total_tokens = len(content) // 4

    # 小文件不拆分
    if total_lines < 2000 and total_tokens < MAX_CONTEXT_TOKENS // 2:
        return [FileChunk(
            name=filename or "full_file",
            content=content,
            line_start=1,
            line_end=total_lines
        )]

    # 尝试按逻辑结构分块
    chunks = chunk_by_class(content, max_chunk_tokens)

    # 如果分块太多（> 50），使用更粗粒度的分块
    if len(chunks) > 50:
        return chunk_by_lines(content, MAX_FILE_CHUNK_LINES * 2, max_chunk_tokens)

    return chunks


def estimate_tokens(content: str, filename: str = "") -> int:
    """
    估算文件内容的 token 数量。

    从 token_counter 导入以避免循环依赖。

    Args:
        content: 文件内容
        filename: 文件名（可选）

    Returns:
        估算的 token 数量
    """
    from .token_counter import estimate_file_tokens
    return estimate_file_tokens(content, filename)
