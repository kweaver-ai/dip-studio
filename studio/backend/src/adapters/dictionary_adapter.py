"""
项目词典适配器

实现 DictionaryPort 接口的 MariaDB 适配器。
"""
import logging
from datetime import datetime
from typing import List, Optional

import aiomysql

from src.domains.dictionary import DictionaryEntry
from src.ports.dictionary_port import DictionaryPort
from src.infrastructure.database.mariadb import MariaDBPool

logger = logging.getLogger(__name__)


class DictionaryAdapter(DictionaryPort):
    """
    项目词典数据库适配器实现。

    该适配器实现了 DictionaryPort 接口，提供词典数据的数据库访问操作。
    """

    def __init__(self, db_pool: MariaDBPool):
        """
        初始化词典适配器。

        参数:
            db_pool: MariaDB 连接池管理器
        """
        self._db_pool = db_pool

    def _row_to_entry(self, row: tuple) -> DictionaryEntry:
        """
        将数据库行转换为词典条目领域模型。

        参数:
            row: 数据库查询结果行
                (id, project_id, term, definition, created_at)

        返回:
            DictionaryEntry: 词典条目领域模型
        """
        return DictionaryEntry(
            id=row[0],
            project_id=row[1],
            term=row[2],
            definition=row[3],
            created_at=row[4],
        )

    async def get_entries_by_project_id(self, project_id: int) -> List[DictionaryEntry]:
        """获取项目的所有词典条目。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, project_id, term, definition, created_at
                       FROM dictionary
                       WHERE project_id = %s
                       ORDER BY term""",
                    (project_id,)
                )
                rows = await cursor.fetchall()
                return [self._row_to_entry(row) for row in rows]

    async def get_entry_by_id(self, entry_id: int) -> DictionaryEntry:
        """根据条目 ID 获取词典条目。"""
        entry = await self.get_entry_by_id_optional(entry_id)
        if entry is None:
            raise ValueError(f"词典条目不存在: id={entry_id}")
        return entry

    async def get_entry_by_id_optional(self, entry_id: int) -> Optional[DictionaryEntry]:
        """根据条目 ID 获取词典条目（可选）。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, project_id, term, definition, created_at
                       FROM dictionary
                       WHERE id = %s""",
                    (entry_id,)
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_entry(row)

    async def get_entry_by_term(self, project_id: int, term: str) -> Optional[DictionaryEntry]:
        """根据术语名称获取词典条目。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, project_id, term, definition, created_at
                       FROM dictionary
                       WHERE project_id = %s AND term = %s""",
                    (project_id, term)
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_entry(row)

    async def create_entry(self, entry: DictionaryEntry) -> DictionaryEntry:
        """创建新的词典条目。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # 检查术语是否已存在
                if await self.check_term_exists(entry.project_id, entry.term):
                    raise ValueError(f"术语在项目中已存在: {entry.term}")

                now = datetime.now()
                await cursor.execute(
                    """INSERT INTO dictionary 
                       (project_id, term, definition, created_at)
                       VALUES (%s, %s, %s, %s)""",
                    (
                        entry.project_id,
                        entry.term,
                        entry.definition,
                        now,
                    )
                )
                entry.id = cursor.lastrowid
                entry.created_at = now
                logger.info(f"创建词典条目成功: id={entry.id}, term={entry.term}")
                return entry

    async def update_entry(self, entry: DictionaryEntry) -> DictionaryEntry:
        """更新词典条目。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # 检查术语是否已被其他条目使用
                if await self.check_term_exists(entry.project_id, entry.term, exclude_id=entry.id):
                    raise ValueError(f"术语在项目中已存在: {entry.term}")

                await cursor.execute(
                    """UPDATE dictionary 
                       SET term = %s, definition = %s
                       WHERE id = %s""",
                    (
                        entry.term,
                        entry.definition,
                        entry.id,
                    )
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"词典条目不存在: id={entry.id}")
                
                logger.info(f"更新词典条目成功: id={entry.id}")
                return entry

    async def delete_entry(self, entry_id: int) -> bool:
        """删除词典条目。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM dictionary WHERE id = %s",
                    (entry_id,)
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"词典条目不存在: id={entry_id}")
                
                logger.info(f"删除词典条目成功: id={entry_id}")
                return True

    async def delete_entries_by_project_id(self, project_id: int) -> int:
        """删除项目的所有词典条目。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM dictionary WHERE project_id = %s",
                    (project_id,)
                )
                count = cursor.rowcount
                logger.info(f"删除项目词典成功: project_id={project_id}, count={count}")
                return count

    async def check_term_exists(
        self,
        project_id: int,
        term: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """检查术语在项目中是否已存在。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if exclude_id:
                    await cursor.execute(
                        """SELECT COUNT(*) FROM dictionary 
                           WHERE project_id = %s AND term = %s AND id != %s""",
                        (project_id, term, exclude_id)
                    )
                else:
                    await cursor.execute(
                        """SELECT COUNT(*) FROM dictionary 
                           WHERE project_id = %s AND term = %s""",
                        (project_id, term)
                    )
                result = await cursor.fetchone()
                return result[0] > 0
