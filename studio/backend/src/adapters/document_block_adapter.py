"""
文档块适配器

实现 DocumentBlockPort 接口的 MariaDB 适配器。
"""
import json
import logging
from datetime import datetime
from typing import List, Optional

from src.domains.document import DocumentBlock, BlockType
from src.ports.document_port import DocumentBlockPort
from src.infrastructure.database.mariadb import MariaDBPool

logger = logging.getLogger(__name__)


def _parse_json(raw) -> Optional[dict]:
    """将 DB 返回的 content（JSON 列）解析为 dict。"""
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw) if raw else None
    return None


class DocumentBlockAdapter(DocumentBlockPort):
    """
    文档块 MariaDB 适配器实现。

    表 document_block：id (PK), document_id, type, content (JSON), order, updated_at。
    领域模型 DocumentBlock.id 为字符串（与 API 兼容），存储为 BIGINT。
    """

    def __init__(self, db_pool: MariaDBPool):
        self._db_pool = db_pool

    def _row_to_block(self, row: tuple) -> DocumentBlock:
        """将数据库行转换为文档块领域模型。row: (id, document_id, type, content, order, updated_at)"""
        return DocumentBlock(
            id=str(row[0]),
            document_id=row[1],
            type=BlockType(row[2]),
            content=_parse_json(row[3]),
            order=row[4] or 0,
            updated_at=row[5],
        )

    async def get_blocks_by_document_id(self, document_id: int) -> List[DocumentBlock]:
        """获取文档的所有块，按 order 排序。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, document_id, type, content, `order`, updated_at
                       FROM document_block
                       WHERE document_id = %s
                       ORDER BY `order`""",
                    (document_id,),
                )
                rows = await cursor.fetchall()
                return [self._row_to_block(row) for row in rows]

    async def get_block_by_id(self, block_id: str) -> Optional[DocumentBlock]:
        """根据块 ID 获取文档块。"""
        try:
            bid = int(block_id)
        except (ValueError, TypeError):
            return None
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, document_id, type, content, `order`, updated_at
                       FROM document_block
                       WHERE id = %s""",
                    (bid,),
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_block(row)

    async def insert_block(self, block: DocumentBlock) -> DocumentBlock:
        """插入新的文档块。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                now = datetime.now()
                content_json = json.dumps(block.content, ensure_ascii=False) if block.content is not None else None
                await cursor.execute(
                    """INSERT INTO document_block (document_id, type, content, `order`, updated_at)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (
                        block.document_id,
                        block.type.value,
                        content_json,
                        block.order,
                        now,
                    ),
                )
                block.id = str(cursor.lastrowid)
                block.updated_at = now
        logger.info(f"插入文档块成功: id={block.id}, document_id={block.document_id}")
        return block

    async def update_block(self, block: DocumentBlock) -> DocumentBlock:
        """更新文档块。"""
        try:
            bid = int(block.id)
        except (ValueError, TypeError):
            raise ValueError(f"文档块不存在: id={block.id}")
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                now = datetime.now()
                content_json = json.dumps(block.content, ensure_ascii=False) if block.content is not None else None
                await cursor.execute(
                    """UPDATE document_block
                       SET content = %s, `order` = %s, updated_at = %s
                       WHERE id = %s""",
                    (content_json, block.order, now, bid),
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"文档块不存在: id={block.id}")
                block.updated_at = now
        logger.info(f"更新文档块成功: id={block.id}")
        return block

    async def delete_block(self, block_id: str) -> bool:
        """删除文档块。"""
        try:
            bid = int(block_id)
        except (ValueError, TypeError):
            return False
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM document_block WHERE id = %s", (bid,))
                if cursor.rowcount > 0:
                    logger.info(f"删除文档块成功: id={block_id}")
                    return True
        return False

    async def delete_blocks_by_document_id(self, document_id: int) -> int:
        """删除文档的所有块。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM document_block WHERE document_id = %s",
                    (document_id,),
                )
                count = cursor.rowcount
        logger.info(f"删除文档块成功: document_id={document_id}, count={count}")
        return count

    async def replace_blocks(
        self,
        document_id: int,
        blocks: List[DocumentBlock],
    ) -> List[DocumentBlock]:
        """用新块列表替换文档的全部块（用于 JSON Patch 应用后的持久化）。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM document_block WHERE document_id = %s",
                    (document_id,),
                )
                now = datetime.now()
                result_blocks: List[DocumentBlock] = []
                for order_index, block in enumerate(blocks):
                    content_json = json.dumps(block.content, ensure_ascii=False) if block.content is not None else None
                    await cursor.execute(
                        """INSERT INTO document_block (document_id, type, content, `order`, updated_at)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (document_id, block.type.value, content_json, order_index, now),
                    )
                    result_blocks.append(
                        DocumentBlock(
                            id=str(cursor.lastrowid),
                            document_id=document_id,
                            type=block.type,
                            content=block.content,
                            order=order_index,
                            updated_at=now,
                        )
                    )
        logger.info(f"replace_blocks: document_id={document_id}, count={len(result_blocks)}")
        return result_blocks

    async def get_max_order(self, document_id: int) -> int:
        """获取文档中块的最大排序值。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT COALESCE(MAX(`order`), 0) FROM document_block WHERE document_id = %s",
                    (document_id,),
                )
                row = await cursor.fetchone()
                return row[0] or 0
