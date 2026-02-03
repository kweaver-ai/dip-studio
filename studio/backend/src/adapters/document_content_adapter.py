"""
文档内容适配器

实现 DocumentContentPort：文档内容以单 JSON 对象存储于 MariaDB。
"""
import copy
import json
import logging
from datetime import datetime
from typing import List

import jsonpatch

from src.ports.document_port import DocumentContentPort
from src.infrastructure.database.mariadb import MariaDBPool

logger = logging.getLogger(__name__)


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
