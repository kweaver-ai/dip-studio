#!/usr/bin/env python3
"""
迁移脚本：将 project_node.id / parent_id 从 BIGINT 改为 UUID v4，
function_document.function_node_id 从 BIGINT 改为 CHAR(36)。

执行前请备份 project_node、function_document。
新表结构建好后，旧表重命名为 _old，新表/列切换为正式名称。
"""
import asyncio
import logging
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import aiomysql

from src.infrastructure.config.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


CREATE_PROJECT_NODE_NEW = """
CREATE TABLE project_node_new (
    id CHAR(36) PRIMARY KEY COMMENT '节点 ID (UUID v4)',
    project_id BIGINT NOT NULL COMMENT '所属项目 ID',
    parent_id CHAR(36) DEFAULT NULL COMMENT '父节点 ID (UUID)',
    node_type VARCHAR(32) NOT NULL COMMENT '节点类型：application/page/function',
    name VARCHAR(255) NOT NULL COMMENT '节点名称',
    description TEXT COMMENT '节点描述',
    path VARCHAR(1024) NOT NULL COMMENT '节点路径，如 /node_<uuid>',
    sort INT DEFAULT 0 COMMENT '同级排序',
    status TINYINT DEFAULT 1 COMMENT '节点状态',
    document_id BIGINT DEFAULT NULL COMMENT '功能节点关联的文档 ID',
    creator_id CHAR(36) DEFAULT NULL COMMENT '创建者用户ID(UUID)',
    creator_name VARCHAR(128) DEFAULT NULL COMMENT '创建者用户显示名',
    created_at DATETIME COMMENT '创建时间',
    editor_id CHAR(36) DEFAULT NULL COMMENT '最近编辑者用户ID(UUID)',
    editor_name VARCHAR(128) DEFAULT NULL COMMENT '最近编辑者用户显示名',
    edited_at DATETIME COMMENT '最近编辑时间',
    INDEX idx_project(project_id),
    INDEX idx_parent(parent_id),
    INDEX idx_path(path(255)),
    INDEX idx_document_id(document_id),
    INDEX idx_creator_id (creator_id),
    INDEX idx_editor_id (editor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目节点表(UUID)';
"""


async def migrate(settings) -> None:
    connection = None
    try:
        connection = await aiomysql.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            db=settings.db_name,
            charset="utf8mb4",
        )
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT id, project_id, parent_id, node_type, name, description, path, sort, status, document_id, creator_id, creator_name, created_at, editor_id, editor_name, edited_at FROM project_node ORDER BY path")
            rows = await cursor.fetchall()
        if not rows:
            logger.info("project_node 表为空，无需迁移")
            return

        old_to_uuid: dict[int, str] = {}
        uuid_to_path: dict[str, str] = {}

        try:
            async with connection.cursor() as cursor:
                await cursor.execute("DROP TABLE IF EXISTS project_node_new")
                await cursor.execute(CREATE_PROJECT_NODE_NEW)

                for row in rows:
                    (old_id, project_id, old_parent_id, node_type, name, description, _path, sort, status, document_id, creator_id, creator_name, created_at, editor_id, editor_name, edited_at) = row
                    new_id = str(uuid.uuid4())
                    old_to_uuid[old_id] = new_id
                    if old_parent_id is None:
                        path = f"/node_{new_id}"
                    else:
                        parent_uuid = old_to_uuid.get(old_parent_id)
                        if parent_uuid is None:
                            raise RuntimeError(f"父节点 {old_parent_id} 未先于子节点处理")
                        path = f"{uuid_to_path[parent_uuid]}/node_{new_id}"
                    uuid_to_path[new_id] = path

                    await cursor.execute(
                        """INSERT INTO project_node_new
                           (id, project_id, parent_id, node_type, name, description, path, sort, status, document_id, creator_id, creator_name, created_at, editor_id, editor_name, edited_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            new_id,
                            project_id,
                            old_to_uuid.get(old_parent_id) if old_parent_id is not None else None,
                            node_type,
                            name or "",
                            description,
                            path,
                            sort or 0,
                            status if status is not None else 1,
                            document_id,
                            creator_id or "",
                            creator_name or "",
                            created_at,
                            editor_id or "",
                            editor_name or "",
                            edited_at,
                        ),
                    )
                count_nodes = len(rows)
                logger.info("project_node_new 插入完成: %s 行", count_nodes)

                await cursor.execute(
                    "ALTER TABLE function_document ADD COLUMN function_node_id_uuid CHAR(36) DEFAULT NULL COMMENT '关联的功能节点 ID (UUID)' AFTER function_node_id"
                )
                for old_nid, new_uuid in old_to_uuid.items():
                    await cursor.execute(
                        "UPDATE function_document SET function_node_id_uuid = %s WHERE function_node_id = %s",
                        (new_uuid, old_nid),
                    )
                await cursor.execute(
                    "ALTER TABLE function_document DROP COLUMN function_node_id"
                )
                await cursor.execute(
                    "ALTER TABLE function_document CHANGE COLUMN function_node_id_uuid function_node_id CHAR(36) NOT NULL COMMENT '关联的功能节点 ID (UUID)'"
                )
                await cursor.execute(
                    "ALTER TABLE function_document ADD UNIQUE KEY uk_function_node_id (function_node_id)"
                )
                logger.info("function_document.function_node_id 已改为 CHAR(36)")

                await cursor.execute("RENAME TABLE project_node TO project_node_old, project_node_new TO project_node")
                logger.info("已切换 project_node 为新表")

            await connection.commit()
        except Exception:
            await connection.rollback()
            raise

        logger.info("✓ 迁移完成。旧表 project_node_old 已保留，确认无误后可手动 DROP。")
    finally:
        if connection:
            connection.close()


async def main() -> None:
    logger.info("=" * 50)
    logger.info("Node ID 迁移：BIGINT -> UUID v4")
    logger.info("=" * 50)
    settings = get_settings()
    await migrate(settings)


if __name__ == "__main__":
    asyncio.run(main())
