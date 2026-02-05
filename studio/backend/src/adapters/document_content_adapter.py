"""
文档内容适配器

实现 DocumentContentPort：文档内容以单 JSON 对象存储于 MariaDB。
TipTap 文档中 paragraph 等节点可能只有 {"type": "paragraph"} 而无 "content"，
应用 JSON Patch 时路径如 /content/12/content/0/text 会因缺少 content 报错，
故在 patch 前对文档做规范化：为可含 content 的节点补上 content: []。
"""
import copy
import json
import logging
from datetime import datetime
from typing import Any, List

import jsonpatch

from src.ports.document_port import DocumentContentPort
from src.infrastructure.database.mariadb import MariaDBPool

logger = logging.getLogger(__name__)

# TipTap 中应有 content 数组的节点类型（缺则补默认，避免 patch 报 member 'content' not found）
_TIPTAP_NODES_WITH_CONTENT = frozenset({
    "doc", "paragraph", "heading", "bulletList", "orderedList", "listItem",
    "blockquote", "codeBlock", "codeBlockLeaf",
})
# 内联节点（paragraph/heading）缺 content 时补一个空 text，使 patch 路径如 /content/0/text 可生效
_INLINE_DEFAULT_CONTENT = [{"type": "text", "text": ""}]


def _ensure_tiptap_content(doc: Any) -> Any:
    """递归为 TipTap 节点补全 content：缺则补 [] 或 paragraph/heading 补空 text，避免 JSON Patch 报错。"""
    if doc is None:
        return None
    if not isinstance(doc, dict):
        return doc
    out = copy.deepcopy(doc)
    node_type = out.get("type") or ""
    if node_type in _TIPTAP_NODES_WITH_CONTENT and "content" not in out:
        # paragraph/heading 常被 patch 到 content/0/text，补默认内联节点
        if node_type in ("paragraph", "heading"):
            out["content"] = copy.deepcopy(_INLINE_DEFAULT_CONTENT)
        else:
            out["content"] = []
    if "content" in out and isinstance(out["content"], list):
        out["content"] = [_ensure_tiptap_content(c) for c in out["content"]]
    return out


class DocumentContentAdapter(DocumentContentPort):
    """
    文档内容 MariaDB 适配器。

    表 document_content：document_id (PK), content (JSON), updated_at。
    """

    def __init__(self, db_pool: MariaDBPool):
        self._db_pool = db_pool

    async def get_content(self, document_id: int) -> dict:
        """获取文档内容，未初始化时返回 {}。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT content FROM document_content WHERE document_id = %s",
                    (document_id,),
                )
                row = await cursor.fetchone()
                if row is None:
                    return {}
                raw = row[0]
                if isinstance(raw, dict):
                    return copy.deepcopy(raw)
                return copy.deepcopy(json.loads(raw)) if raw else {}

    async def set_content(self, document_id: int, content: dict) -> None:
        """设置文档内容（初始化或覆盖）。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                now = datetime.now()
                payload = copy.deepcopy(content) if content is not None else {}
                content_json = json.dumps(payload, ensure_ascii=False)
                await cursor.execute(
                    """INSERT INTO document_content (document_id, content, updated_at)
                       VALUES (%s, %s, %s)
                       ON DUPLICATE KEY UPDATE content = VALUES(content), updated_at = VALUES(updated_at)""",
                    (document_id, content_json, now),
                )
        logger.info(f"set_content: document_id={document_id}")

    async def patch_content(
        self,
        document_id: int,
        patch_operations: List[dict],
    ) -> dict:
        """对文档内容应用 JSON Patch 并持久化，返回新内容。"""
        current = await self.get_content(document_id)
        # 规范化：为 paragraph 等节点补上缺失的 content，避免 patch 路径如 /content/12/content/0/text 报 member 'content' not found
        current = _ensure_tiptap_content(current) if current else {}
        try:
            new_content = jsonpatch.apply_patch(current, patch_operations)
        except jsonpatch.JsonPatchException as e:
            raise ValueError(f"JSON Patch 应用失败: {e}") from e
        if not isinstance(new_content, dict):
            raise ValueError("Patch 结果必须为 JSON 对象")
        await self.set_content(document_id, new_content)
        return new_content

    async def delete_content(self, document_id: int) -> None:
        """删除文档内容（按 document_id）。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM document_content WHERE document_id = %s",
                    (document_id,),
                )
                if cursor.rowcount:
                    logger.info(f"delete_content: document_id={document_id}")
