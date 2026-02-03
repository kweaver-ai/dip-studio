"""
节点适配器

实现 NodePort 接口的 MariaDB 适配器。
"""
import logging
from datetime import datetime
from typing import List, Optional

import aiomysql

from src.domains.node import ProjectNode, NodeType
from src.ports.node_port import NodePort
from src.infrastructure.database.mariadb import MariaDBPool

logger = logging.getLogger(__name__)


class NodeAdapter(NodePort):
    """
    节点数据库适配器实现。

    该适配器实现了 NodePort 接口，提供节点数据的数据库访问操作。
    """

    def __init__(self, db_pool: MariaDBPool):
        """
        初始化节点适配器。

        参数:
            db_pool: MariaDB 连接池管理器
        """
        self._db_pool = db_pool

    def _row_to_node(self, row: tuple) -> ProjectNode:
        """
        将数据库行转换为节点领域模型。

        参数:
            row: 数据库查询结果行 (含 document_id 时为 14 列，无 mode)

        返回:
            ProjectNode: 节点领域模型
        """
        # 兼容无 document_id 的旧表（行长为 13）
        document_id = row[13] if len(row) > 13 else None
        return ProjectNode(
            id=row[0],
            project_id=row[1],
            parent_id=row[2],
            node_type=NodeType(row[3]),
            name=row[4],
            description=row[5],
            path=row[6],
            sort=row[7],
            status=row[8] if row[8] is not None else 1,
            creator=row[9],
            created_at=row[10],
            editor=row[11],
            edited_at=row[12],
            document_id=document_id,
        )

    async def get_node_by_id(self, node_id: int) -> ProjectNode:
        """根据节点 ID 获取节点信息。"""
        node = await self.get_node_by_id_optional(node_id)
        if node is None:
            raise ValueError(f"节点不存在: id={node_id}")
        return node

    async def get_node_by_id_optional(self, node_id: int) -> Optional[ProjectNode]:
        """根据节点 ID 获取节点信息（可选）。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, project_id, parent_id, node_type, name, description,
                              path, sort, status, creator, created_at, editor, edited_at,
                              document_id
                       FROM project_node
                       WHERE id = %s""",
                    (node_id,)
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_node(row)

    async def get_nodes_by_project_id(self, project_id: int) -> List[ProjectNode]:
        """获取项目下的所有节点。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, project_id, parent_id, node_type, name, description,
                              path, sort, status, creator, created_at, editor, edited_at,
                              document_id
                       FROM project_node
                       WHERE project_id = %s
                       ORDER BY path, sort""",
                    (project_id,)
                )
                rows = await cursor.fetchall()
                return [self._row_to_node(row) for row in rows]

    async def get_root_node(self, project_id: int) -> Optional[ProjectNode]:
        """获取项目的根节点（应用节点）。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, project_id, parent_id, node_type, name, description,
                              path, sort, status, creator, created_at, editor, edited_at,
                              document_id
                       FROM project_node
                       WHERE project_id = %s AND parent_id IS NULL AND node_type = %s""",
                    (project_id, NodeType.APPLICATION.value)
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_node(row)

    async def get_children(self, node_id: int) -> List[ProjectNode]:
        """获取节点的直接子节点。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id, project_id, parent_id, node_type, name, description,
                              path, sort, status, creator, created_at, editor, edited_at,
                              document_id
                       FROM project_node
                       WHERE parent_id = %s
                       ORDER BY sort""",
                    (node_id,)
                )
                rows = await cursor.fetchall()
                return [self._row_to_node(row) for row in rows]

    async def get_descendants(self, node_id: int) -> List[ProjectNode]:
        """获取节点的所有后代节点。"""
        # 首先获取当前节点的路径
        node = await self.get_node_by_id_optional(node_id)
        if node is None:
            return []
        
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # 使用路径前缀查询所有后代
                await cursor.execute(
                    """SELECT id, project_id, parent_id, node_type, name, description,
                              path, sort, status, creator, created_at, editor, edited_at,
                              document_id
                       FROM project_node
                       WHERE path LIKE %s AND id != %s
                       ORDER BY path, sort""",
                    (f"{node.path}/%", node_id)
                )
                rows = await cursor.fetchall()
                return [self._row_to_node(row) for row in rows]

    async def has_children(self, node_id: int) -> bool:
        """检查节点是否有子节点。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT COUNT(*) FROM project_node WHERE parent_id = %s",
                    (node_id,)
                )
                result = await cursor.fetchone()
                return result[0] > 0

    async def create_node(self, node: ProjectNode) -> ProjectNode:
        """创建新节点。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                now = datetime.now()
                await cursor.execute(
                    """INSERT INTO project_node 
                       (project_id, parent_id, node_type, name, description, path, sort, 
                        status, creator, created_at, editor, edited_at, document_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        node.project_id,
                        node.parent_id,
                        node.node_type.value,
                        node.name,
                        node.description,
                        node.path or "",  # 临时路径，创建后更新
                        node.sort,
                        node.status,
                        node.creator,
                        now,
                        node.editor or node.creator,
                        now,
                        node.document_id,
                    )
                )
                node.id = cursor.lastrowid
                node.created_at = now
                node.edited_at = now
                
                # 更新节点路径
                if node.parent_id:
                    parent = await self.get_node_by_id(node.parent_id)
                    node.path = f"{parent.path}/node_{node.id}"
                else:
                    node.path = f"/node_{node.id}"
                
                await cursor.execute(
                    "UPDATE project_node SET path = %s WHERE id = %s",
                    (node.path, node.id)
                )
                
                logger.info(f"创建节点成功: id={node.id}, type={node.node_type.value}")
                return node

    async def update_node_document_id(self, node_id: int, document_id: int) -> bool:
        """更新功能节点关联的文档 ID。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE project_node SET document_id = %s WHERE id = %s",
                    (document_id, node_id)
                )
                return cursor.rowcount > 0

    async def update_node(self, node: ProjectNode) -> ProjectNode:
        """更新节点信息。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                now = datetime.now()
                await cursor.execute(
                    """UPDATE project_node 
                       SET name = %s, description = %s, sort = %s,
                           editor = %s, edited_at = %s
                       WHERE id = %s""",
                    (
                        node.name,
                        node.description,
                        node.sort,
                        node.editor,
                        now,
                        node.id,
                    )
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"节点不存在: id={node.id}")
                
                node.edited_at = now
                logger.info(f"更新节点成功: id={node.id}")
                return node

    async def update_node_path(self, node_id: int, new_path: str) -> bool:
        """更新节点路径。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE project_node SET path = %s WHERE id = %s",
                    (new_path, node_id)
                )
                return cursor.rowcount > 0

    async def update_descendants_path(
        self,
        node_id: int,
        old_path: str,
        new_path: str,
    ) -> int:
        """更新所有后代节点的路径。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # 使用 REPLACE 更新路径前缀
                await cursor.execute(
                    """UPDATE project_node 
                       SET path = CONCAT(%s, SUBSTRING(path, %s))
                       WHERE path LIKE %s AND id != %s""",
                    (new_path, len(old_path) + 1, f"{old_path}/%", node_id)
                )
                return cursor.rowcount

    async def move_node(
        self,
        node_id: int,
        new_parent_id: Optional[int],
        new_sort: int,
    ) -> ProjectNode:
        """移动节点到新的父节点下；先对同级 sort >= new_sort 的节点 +1 腾位，再写入新 sort。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                node = await self.get_node_by_id(node_id)
                old_path = node.path

                if new_parent_id:
                    parent = await self.get_node_by_id(new_parent_id)
                    new_path = f"{parent.path}/node_{node.id}"
                else:
                    new_path = f"/node_{node.id}"

                now = datetime.now()
                # 先对同级中 sort >= new_sort 的节点（排除当前节点）执行 sort+1 腾出位置
                if new_parent_id is not None:
                    await cursor.execute(
                        """UPDATE project_node
                           SET sort = sort + 1
                           WHERE parent_id = %s AND id != %s AND sort >= %s""",
                        (new_parent_id, node_id, new_sort),
                    )
                else:
                    await cursor.execute(
                        """UPDATE project_node
                           SET sort = sort + 1
                           WHERE project_id = %s AND parent_id IS NULL AND id != %s AND sort >= %s""",
                        (node.project_id, node_id, new_sort),
                    )

                await cursor.execute(
                    """UPDATE project_node 
                       SET parent_id = %s, path = %s, sort = %s, edited_at = %s
                       WHERE id = %s""",
                    (new_parent_id, new_path, new_sort, now, node_id),
                )

                await self.update_descendants_path(node_id, old_path, new_path)

                node.parent_id = new_parent_id
                node.path = new_path
                node.sort = new_sort
                node.edited_at = now

                logger.info(f"移动节点成功: id={node_id}, new_parent_id={new_parent_id}")
                return node

    async def delete_node(self, node_id: int) -> bool:
        """删除节点。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM project_node WHERE id = %s",
                    (node_id,)
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"节点不存在: id={node_id}")
                
                logger.info(f"删除节点成功: id={node_id}")
                return True

    async def delete_nodes_by_project_id(self, project_id: int) -> int:
        """删除项目下的所有节点。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM project_node WHERE project_id = %s",
                    (project_id,)
                )
                count = cursor.rowcount
                logger.info(f"删除项目节点成功: project_id={project_id}, count={count}")
                return count

    async def get_max_sort(self, parent_id: Optional[int], project_id: int) -> int:
        """获取同级节点的最大排序值。"""
        pool = await self._db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if parent_id:
                    await cursor.execute(
                        "SELECT COALESCE(MAX(sort), 0) FROM project_node WHERE parent_id = %s",
                        (parent_id,)
                    )
                else:
                    await cursor.execute(
                        """SELECT COALESCE(MAX(sort), 0) FROM project_node 
                           WHERE project_id = %s AND parent_id IS NULL""",
                        (project_id,)
                    )
                result = await cursor.fetchone()
                return result[0]
