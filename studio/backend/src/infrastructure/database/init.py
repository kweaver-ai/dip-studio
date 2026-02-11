"""
数据库初始化模块

在服务启动时自动检测并创建所需的数据库表。
严格参考 hub/backend 的 src/infrastructure/database/init.py 实现。
"""
import logging
from typing import Optional

import aiomysql

from src.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


async def ensure_tables_exist(settings: Settings) -> None:
    """
    确保所有必需的数据库表存在，如果不存在则创建。

    参数:
        settings: 应用配置
    """
    connection: Optional[aiomysql.Connection] = None
    try:
        # 先连接到 MySQL（不指定数据库），以便创建库
        connection = await aiomysql.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            charset="utf8mb4",
        )

        async with connection.cursor() as cursor:
            # 创建数据库（如果不存在）并选中
            await cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            await cursor.execute(f"USE `{settings.db_name}`")
            logger.info(f"数据库 '{settings.db_name}' 已就绪")

            # 项目表
            await _ensure_table_exists(
                cursor,
                settings.db_name,
                "project",
                """
                CREATE TABLE IF NOT EXISTS project (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(128) NOT NULL UNIQUE COMMENT '项目名称',
                    description VARCHAR(400) COMMENT '项目描述',
                    creator_id CHAR(36) NOT NULL COMMENT '创建者用户ID(UUID)',
                    creator_name VARCHAR(128) NOT NULL COMMENT '创建者用户显示名',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    editor_id CHAR(36) NOT NULL COMMENT '最近编辑者用户ID(UUID)',
                    editor_name VARCHAR(128) NOT NULL COMMENT '最近编辑者用户显示名',
                    edited_at DATETIME NOT NULL COMMENT '最近编辑时间',
                    INDEX idx_creator_id (creator_id),
                    INDEX idx_editor_id (editor_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目表'
                """,
            )

            # 项目节点表
            await _ensure_table_exists(
                cursor,
                settings.db_name,
                "project_node",
                """
                CREATE TABLE IF NOT EXISTS project_node (
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目节点表'
                """,
            )

            # 节点类型约束表
            await _ensure_table_exists(
                cursor,
                settings.db_name,
                "node_type",
                """
                CREATE TABLE IF NOT EXISTS node_type (
                    code VARCHAR(32) PRIMARY KEY COMMENT '节点类型代码',
                    name VARCHAR(64) COMMENT '节点类型名称',
                    parent_allow VARCHAR(255) COMMENT '允许的父节点类型，逗号分隔'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节点类型约束表'
                """,
            )

            # 功能设计文档表
            await _ensure_table_exists(
                cursor,
                settings.db_name,
                "function_document",
                """
                CREATE TABLE IF NOT EXISTS function_document (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    function_node_id CHAR(36) UNIQUE NOT NULL COMMENT '关联的功能节点 ID (UUID)',
                    creator_id CHAR(36) DEFAULT NULL COMMENT '创建者用户ID(UUID)',
                    creator_name VARCHAR(128) DEFAULT NULL COMMENT '创建者用户显示名',
                    created_at DATETIME COMMENT '创建时间',
                    editor_id CHAR(36) DEFAULT NULL COMMENT '最近编辑者用户ID(UUID)',
                    editor_name VARCHAR(128) DEFAULT NULL COMMENT '最近编辑者用户显示名',
                    edited_at DATETIME COMMENT '最近编辑时间'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='功能设计文档表'
                """,
            )

            # 项目词典表
            await _ensure_table_exists(
                cursor,
                settings.db_name,
                "dictionary",
                """
                CREATE TABLE IF NOT EXISTS dictionary (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    project_id BIGINT NOT NULL COMMENT '所属项目 ID',
                    term VARCHAR(255) NOT NULL COMMENT '术语名称',
                    definition TEXT NOT NULL COMMENT '术语定义',
                    creator_id CHAR(36) DEFAULT NULL COMMENT '创建者用户ID(UUID)',
                    creator_name VARCHAR(128) DEFAULT NULL COMMENT '创建者用户显示名',
                    created_at DATETIME COMMENT '创建时间',
                    editor_id CHAR(36) DEFAULT NULL COMMENT '最近编辑者用户ID(UUID)',
                    editor_name VARCHAR(128) DEFAULT NULL COMMENT '最近编辑者用户显示名',
                    edited_at DATETIME COMMENT '最近编辑时间',
                    UNIQUE KEY uk_project_term(project_id, term)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目词典表'
                """,
            )

            # 文档内容表
            await _ensure_table_exists(
                cursor,
                settings.db_name,
                "document_content",
                """
                CREATE TABLE IF NOT EXISTS document_content (
                    document_id BIGINT PRIMARY KEY COMMENT '文档 ID，关联 function_document.id',
                    content JSON NOT NULL COMMENT '文档内容（单 JSON 对象）',
                    updated_at DATETIME NOT NULL COMMENT '更新时间'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档内容表'
                """,
            )

            # 文档块表
            await _ensure_table_exists(
                cursor,
                settings.db_name,
                "document_block",
                """
                CREATE TABLE IF NOT EXISTS document_block (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '块 ID',
                    document_id BIGINT NOT NULL COMMENT '文档 ID',
                    type VARCHAR(32) NOT NULL COMMENT '块类型：text/list/table/plugin',
                    content JSON COMMENT '块内容',
                    `order` INT NOT NULL DEFAULT 0 COMMENT '排序',
                    updated_at DATETIME COMMENT '更新时间',
                    INDEX idx_document_order (document_id, `order`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档块表'
                """,
            )

            # 初始化节点类型数据
            await cursor.execute(
                """
                INSERT IGNORE INTO node_type (code, name, parent_allow) VALUES
                    ('application', '应用', NULL),
                    ('page', '页面', 'application'),
                    ('function', '功能', 'page')
                """
            )

            # 迁移：为已存在的 project_node 表添加 document_id 列（若不存在）
            await _ensure_column_exists(
                cursor,
                settings.db_name,
                "project_node",
                "document_id",
                "ALTER TABLE project_node ADD COLUMN document_id BIGINT DEFAULT NULL "
                "COMMENT '功能节点关联的文档 ID' AFTER status",
            )

        await connection.commit()
        logger.info("数据库表检查完成")

    except Exception as e:
        logger.error(f"数据库表初始化失败: {e}", exc_info=True)
        if connection:
            await connection.rollback()
        raise
    finally:
        if connection:
            connection.close()


async def _ensure_table_exists(
    cursor: aiomysql.Cursor,
    db_name: str,
    table_name: str,
    create_sql: str,
) -> None:
    """
    确保表存在，如果不存在则创建。

    参数:
        cursor: 数据库游标
        db_name: 数据库名称
        table_name: 表名
        create_sql: 创建表的 SQL 语句
    """
    try:
        await cursor.execute(
            """
            SELECT COUNT(*) as cnt
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """,
            (db_name, table_name),
        )
        result = await cursor.fetchone()
        count = result[0] if result else 0

        if count == 0:
            await cursor.execute(create_sql)
            logger.info(f"✓ 表 '{table_name}' 已创建")
        else:
            logger.debug(f"○ 表 '{table_name}' 已存在")
    except Exception as e:
        logger.error(f"检查/创建表 '{table_name}' 失败: {e}", exc_info=True)
        raise


async def _ensure_column_exists(
    cursor: aiomysql.Cursor,
    db_name: str,
    table_name: str,
    column_name: str,
    alter_sql: str,
) -> None:
    """
    确保列存在，如果不存在则添加。

    参数:
        cursor: 数据库游标
        db_name: 数据库名称
        table_name: 表名
        column_name: 列名
        alter_sql: 添加列的 SQL 语句
    """
    try:
        await cursor.execute(
            """
            SELECT COUNT(*) as cnt
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            AND COLUMN_NAME = %s
            """,
            (db_name, table_name, column_name),
        )
        result = await cursor.fetchone()
        count = result[0] if result else 0

        if count == 0:
            await cursor.execute(alter_sql)
            logger.info(f"✓ 表 '{table_name}' 的列 '{column_name}' 已添加")
        else:
            logger.debug(f"○ 表 '{table_name}' 的列 '{column_name}' 已存在")
    except Exception as e:
        logger.warning(f"检查/添加列 '{table_name}.{column_name}' 失败: {e}")
