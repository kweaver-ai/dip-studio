"""
功能设计文档适配器

实现 DocumentPort 接口的 MariaDB 适配器。
"""
import logging
from datetime import datetime
from typing import Optional

import aiomysql

from src.domains.document import FunctionDocument
from src.ports.document_port import DocumentPort
from src.infrastructure.database.mariadb import MariaDBPool

logger = logging.getLogger(__name__)


class DocumentAdapter(DocumentPort):
    """
    功能设计文档数据库适配器实现。

    该适配器实现了 DocumentPort 接口，提供文档元信息的数据库访问操作。
    """

    def __init__(self, db_pool: MariaDBPool):
        """
        初始化文档适配器。

        参数:
            db_pool: MariaDB 连接池管理器
        """
        self._db_pool = db_pool

    def _row_to_document(self, row: tuple) -> FunctionDocument:
        """
        将数据库行转换为文档领域模型。

        参数:
            row: 数据库查询结果行
                (id, function_node_id, creator_id, creator_name, created_at, editor_id, editor_name, edited_at)

        返回:
            FunctionDocument: 文档领域模型
        """
        return FunctionDocument(
            id=row[0],
            function_node_id=str(row[1]) if row[1] is not None else "",
            creator_id=row[2] or "",
            creator_name=row[3] or "",
            created_at=row[4],
            editor_id=row[5] or "",
            editor_name=row[6] or "",
            edited_at=row[7],
        )

    async def get_document_by_id(self, document_id: int) -> FunctionDocument:
        """根据文档 ID 获取文档。"""
        document = await self.get_document_by_id_optional(document_id)
        if document is None:
            raise ValueError(f"文档不存在: id={document_id}")
        return document

    async def get_document_by_id_optional(self, document_id: int) -> Optional[FunctionDocument]:
        """根据文档 ID 获取文档（可选）。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, function_node_id, creator_id, creator_name, created_at, editor_id, editor_name, edited_at
                       FROM function_document
                       WHERE id = %s""",
                    (document_id,)
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_document(row)

    async def get_document_by_node_id(self, function_node_id: str) -> Optional[FunctionDocument]:
        """根据功能节点 ID 获取文档。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, function_node_id, creator_id, creator_name, created_at, editor_id, editor_name, edited_at
                       FROM function_document
                       WHERE function_node_id = %s""",
                    (function_node_id,)
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_document(row)

    async def create_document(self, document: FunctionDocument) -> FunctionDocument:
        """创建新文档。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                now = datetime.now()
                await cursor.execute(
                    """INSERT INTO function_document 
                       (function_node_id, creator_id, creator_name, created_at, editor_id, editor_name, edited_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        document.function_node_id,
                        document.creator_id,
                        document.creator_name,
                        now,
                        document.editor_id or document.creator_id,
                        document.editor_name or document.creator_name,
                        now,
                    )
                )
                document.id = cursor.lastrowid
                document.created_at = now
                document.edited_at = now
                logger.info(f"创建文档成功: id={document.id}, node_id={document.function_node_id}")
                return document

    async def update_document(self, document: FunctionDocument) -> FunctionDocument:
        """更新文档信息。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                now = datetime.now()
                await cursor.execute(
                    """UPDATE function_document 
                       SET editor_id = %s, editor_name = %s, edited_at = %s
                       WHERE id = %s""",
                    (
                        document.editor_id,
                        document.editor_name,
                        now,
                        document.id,
                    )
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"文档不存在: id={document.id}")
                
                document.edited_at = now
                logger.info(f"更新文档成功: id={document.id}")
                return document

    async def delete_document(self, document_id: int) -> bool:
        """删除文档。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM function_document WHERE id = %s",
                    (document_id,)
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"文档不存在: id={document_id}")
                
                logger.info(f"删除文档成功: id={document_id}")
                return True

    async def delete_document_by_node_id(self, function_node_id: str) -> bool:
        """根据功能节点 ID 删除文档。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM function_document WHERE function_node_id = %s",
                    (function_node_id,)
                )
                if cursor.rowcount > 0:
                    logger.info(f"删除文档成功: node_id={function_node_id}")
                return True
