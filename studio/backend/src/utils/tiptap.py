"""
TipTap 文档 JSON 转可读文本

将 TipTap 编辑器的 JSON 结构转为适合 Coding Agent / MCP 使用的纯文本（类 Markdown），
便于根据文档内容生成代码或理解需求。
"""
from typing import Any, List


def tiptap_json_to_readable_text(doc: Any) -> str:
    """
    将 TipTap 文档 JSON 转为可读文本（类 Markdown）。

    支持常见节点：doc, paragraph, text, heading, bulletList, orderedList,
    listItem, blockquote, codeBlock。其他节点按内容递归拼接。

    参数:
        doc: TipTap 文档根（dict，通常 type="doc"）或任意节点

    返回:
        str: 可读文本，空文档返回空字符串
    """
    if doc is None:
        return ""
    if not isinstance(doc, dict):
        return str(doc)
    node_type = doc.get("type") or ""
    content = doc.get("content")
    content_list = content if isinstance(content, list) else []

    if node_type == "text":
        return (doc.get("text") or "").strip()

    if node_type == "doc":
        return _join_blocks(content_list).strip()

    if node_type == "paragraph":
        return _inline_text(content_list) + "\n"

    if node_type == "heading":
        level = 1
        attrs = doc.get("attrs") or {}
        if isinstance(attrs, dict):
            level = max(1, min(6, int(attrs.get("level") or 1)))
        return "#" * level + " " + _inline_text(content_list).strip() + "\n"

    if node_type == "bulletList":
        return _list_items(content_list, bullet="- ") + "\n"

    if node_type == "orderedList":
        return _list_items(content_list, ordered=True) + "\n"

    if node_type == "listItem":
        raw = _join_blocks(content_list).strip().replace("\n", "\n  ")
        return raw + "\n" if raw else ""

    if node_type == "blockquote":
        raw = _join_blocks(content_list).strip()
        return "\n".join("> " + line for line in raw.split("\n")) + "\n"

    if node_type == "codeBlock":
        raw = _inline_text(content_list)
        lang = ""
        attrs = doc.get("attrs") or {}
        if isinstance(attrs, dict):
            lang = (attrs.get("language") or "").strip()
        if lang:
            return f"```{lang}\n{raw}\n```\n"
        return f"```\n{raw}\n```\n"

    if node_type == "horizontalRule":
        return "---\n"

    # 默认：递归处理 content 并拼接
    return _join_blocks(content_list)


def _inline_text(nodes: List[Any]) -> str:
    """将内联节点列表（如 paragraph 的 content）转为一行文本。"""
    parts = []
    for n in nodes or []:
        if not isinstance(n, dict):
            continue
        if n.get("type") == "text":
            parts.append(n.get("text") or "")
        elif n.get("type") == "hardBreak":
            parts.append("\n")
        else:
            parts.append(tiptap_json_to_readable_text(n))
    return "".join(parts).replace("\n\n", "\n")


def _join_blocks(nodes: List[Any]) -> str:
    """将块级节点列表拼接为一段文本。"""
    parts = []
    for n in nodes or []:
        parts.append(tiptap_json_to_readable_text(n))
    return "".join(parts)


def _list_items(nodes: List[Any], bullet: str = "- ", ordered: bool = False) -> str:
    """列表项拼接：listItem 内容前加 - 或 1. 2. ..."""
    lines = []
    for i, n in enumerate(nodes or []):
        raw = tiptap_json_to_readable_text(n).strip()
        if not raw:
            continue
        prefix = f"{i + 1}. " if ordered else bullet
        for j, line in enumerate(raw.split("\n")):
            lines.append((prefix + line) if line else "")
            prefix = "  " if ordered else "  "
    return "\n".join(lines)
