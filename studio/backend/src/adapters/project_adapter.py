"""
项目适配器

实现 ProjectPort 接口的 MariaDB 适配器。
"""
import logging
from datetime import datetime
from typing import List, Optional

import aiomysql

from src.domains.project import Project
from src.ports.project_port import ProjectPort
from src.infrastructure.database.mariadb import MariaDBPool

logger = logging.getLogger(__name__)


class ProjectAdapter(ProjectPort):
    """
    项目数据库适配器实现。

    该适配器实现了 ProjectPort 接口，提供项目数据的数据库访问操作。
    """

    def __init__(self, db_pool: MariaDBPool):
        """
        初始化项目适配器。

        参数:
            db_pool: MariaDB 连接池管理器
        """
        self._db_pool = db_pool

    def _row_to_project(self, row: tuple) -> Project:
        """
        将数据库行转换为项目领域模型。

        参数:
            row: 数据库查询结果行
                (id, name, description, creator, created_at, editor, edited_at)

        返回:
            Project: 项目领域模型
        """
        return Project(
            id=row[0],
            name=row[1],
            description=row[2],
            creator=row[3],
            created_at=row[4],
            editor=row[5],
            edited_at=row[6],
        )

    async def get_all_projects(self) -> List[Project]:
        """获取所有项目列表。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, name, description, creator, created_at, editor, edited_at
                       FROM project
                       ORDER BY edited_at DESC"""
                )
                rows = await cursor.fetchall()
                return [self._row_to_project(row) for row in rows]

    async def get_project_by_id(self, project_id: int) -> Project:
        """根据项目 ID 获取项目信息。"""
        project = await self.get_project_by_id_optional(project_id)
        if project is None:
            raise ValueError(f"项目不存在: id={project_id}")
        return project

    async def get_project_by_id_optional(self, project_id: int) -> Optional[Project]:
        """根据项目 ID 获取项目信息（可选）。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, name, description, creator, created_at, editor, edited_at
                       FROM project
                       WHERE id = %s""",
                    (project_id,)
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_project(row)

    async def get_project_by_name(self, name: str) -> Optional[Project]:
        """根据项目名称获取项目信息。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, name, description, creator, created_at, editor, edited_at
                       FROM project
                       WHERE name = %s""",
                    (name,)
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_project(row)

    async def create_project(self, project: Project) -> Project:
        """创建新项目。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # 检查项目名称是否已存在
                if await self.check_name_exists(project.name):
                    raise ValueError(f"项目名称已存在: {project.name}")

                now = datetime.now()
                await cursor.execute(
                    """INSERT INTO project 
                       (name, description, creator, created_at, editor, edited_at)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        project.name,
                        project.description,
                        project.creator,
                        now,
                        project.editor or project.creator,
                        now,
                    )
                )
                project.id = cursor.lastrowid
                project.created_at = now
                project.edited_at = now
                logger.info(f"创建项目成功: id={project.id}, name={project.name}")
                return project

    async def update_project(self, project: Project) -> Project:
        """更新项目信息。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # 检查项目名称是否已被其他项目使用
                if await self.check_name_exists(project.name, exclude_id=project.id):
                    raise ValueError(f"项目名称已存在: {project.name}")

                now = datetime.now()
                await cursor.execute(
                    """UPDATE project 
                       SET name = %s, description = %s, editor = %s, edited_at = %s
                       WHERE id = %s""",
                    (
                        project.name,
                        project.description,
                        project.editor,
                        now,
                        project.id,
                    )
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"项目不存在: id={project.id}")
                
                project.edited_at = now
                logger.info(f"更新项目成功: id={project.id}")
                return project

    async def delete_project(self, project_id: int) -> bool:
        """删除项目。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM project WHERE id = %s",
                    (project_id,)
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"项目不存在: id={project_id}")
                
                logger.info(f"删除项目成功: id={project_id}")
                return True

    async def check_name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """检查项目名称是否已存在。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if exclude_id:
                    await cursor.execute(
                        "SELECT COUNT(*) FROM project WHERE name = %s AND id != %s",
                        (name, exclude_id)
                    )
                else:
                    await cursor.execute(
                        "SELECT COUNT(*) FROM project WHERE name = %s",
                        (name,)
                    )
                result = await cursor.fetchone()
                return result[0] > 0
