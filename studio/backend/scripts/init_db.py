#!/usr/bin/env python3
"""
数据库初始化脚本

在服务启动前创建所需的数据库表和初始数据。
"""
import asyncio
import logging
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import aiomysql

from src.infrastructure.config.settings import get_settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# MariaDB 建表语句
CREATE_TABLES_SQL = """
-- 项目表
CREATE TABLE IF NOT EXISTS project (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(128) NOT NULL UNIQUE COMMENT '项目名称',
    description VARCHAR(400) COMMENT '项目描述',
    creator BIGINT NOT NULL COMMENT '创建者用户 ID',
    created_at DATETIME NOT NULL COMMENT '创建时间',
    editor BIGINT NOT NULL COMMENT '最近编辑者用户 ID',
    edited_at DATETIME NOT NULL COMMENT '最近编辑时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目表';

-- 节点表 (统一管理 application/page/function)
CREATE TABLE IF NOT EXISTS project_node (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '所属项目 ID',
    parent_id BIGINT DEFAULT NULL COMMENT '父节点 ID',
    node_type VARCHAR(32) NOT NULL COMMENT '节点类型：application/page/function',
    name VARCHAR(255) NOT NULL COMMENT '节点名称',
    description TEXT COMMENT '节点描述',
    path VARCHAR(1024) NOT NULL COMMENT '节点路径，如 /node_1/node_3/node_8',
    sort INT DEFAULT 0 COMMENT '同级排序',
    status TINYINT DEFAULT 1 COMMENT '节点状态',
    document_id BIGINT DEFAULT NULL COMMENT '功能节点关联的文档 ID',
    creator BIGINT COMMENT '创建者用户 ID',
    created_at DATETIME COMMENT '创建时间',
    editor BIGINT COMMENT '最近编辑者用户 ID',
    edited_at DATETIME COMMENT '最近编辑时间',
    INDEX idx_project(project_id),
    INDEX idx_parent(parent_id),
    INDEX idx_path(path(255)),
    INDEX idx_document_id(document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目节点表';

-- 节点类型约束表
CREATE TABLE IF NOT EXISTS node_type (
    code VARCHAR(32) PRIMARY KEY COMMENT '节点类型代码',
    name VARCHAR(64) COMMENT '节点类型名称',
    parent_allow VARCHAR(255) COMMENT '允许的父节点类型，逗号分隔'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节点类型约束表';

-- 功能设计文档表
CREATE TABLE IF NOT EXISTS function_document (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    function_node_id BIGINT UNIQUE NOT NULL COMMENT '关联的功能节点 ID',
    creator BIGINT COMMENT '创建者用户 ID',
    created_at DATETIME COMMENT '创建时间',
    editor BIGINT COMMENT '最近编辑者用户 ID',
    edited_at DATETIME COMMENT '最近编辑时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='功能设计文档表';

-- 项目词典表
CREATE TABLE IF NOT EXISTS dictionary (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '所属项目 ID',
    term VARCHAR(255) NOT NULL COMMENT '术语名称',
    definition TEXT NOT NULL COMMENT '术语定义',
    created_at DATETIME COMMENT '创建时间',
    UNIQUE KEY uk_project_term(project_id, term)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目词典表';

-- 文档内容表（单 JSON 对象 per document，替代原 MongoDB document_content）
CREATE TABLE IF NOT EXISTS document_content (
    document_id BIGINT PRIMARY KEY COMMENT '文档 ID，关联 function_document.id',
    content JSON NOT NULL COMMENT '文档内容（单 JSON 对象）',
    updated_at DATETIME NOT NULL COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档内容表';

-- 文档块表（替代原 MongoDB document_block）
CREATE TABLE IF NOT EXISTS document_block (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '块 ID',
    document_id BIGINT NOT NULL COMMENT '文档 ID',
    type VARCHAR(32) NOT NULL COMMENT '块类型：text/list/table/plugin',
    content JSON COMMENT '块内容',
    `order` INT NOT NULL DEFAULT 0 COMMENT '排序',
    updated_at DATETIME COMMENT '更新时间',
    INDEX idx_document_order (document_id, `order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档块表';
"""

# 初始数据
INIT_DATA_SQL = """
-- 初始化节点类型约束数据
INSERT IGNORE INTO node_type (code, name, parent_allow) VALUES
    ('application', '应用', NULL),
    ('page', '页面', 'application'),
    ('function', '功能', 'page');
"""


async def init_mariadb(settings):
    """
    初始化 MariaDB 数据库。
    
    参数:
        settings: 应用配置
    """
    logger.info("开始初始化 MariaDB 数据库...")
    logger.info(f"连接到 {settings.db_host}:{settings.db_port}/{settings.db_name}")
    
    connection = None
    try:
        # 连接到数据库
        connection = await aiomysql.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            db=settings.db_name,
            charset='utf8mb4',
        )
        
        async with connection.cursor() as cursor:
            # 再次显式选择数据库，避免某些环境下默认库不正确
            await cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` CHARACTER SET utf8mb4")
            await cursor.execute(f"USE `{settings.db_name}`")

            # 执行建表语句（如有错误直接抛出，而不是静默忽略）
            for raw in CREATE_TABLES_SQL.split(';'):
                # 去掉每条语句内部的注释行（以 -- 开头），避免把注释和 SQL 混在一起导致整条被跳过
                lines = []
                for line in raw.splitlines():
                    if line.strip().startswith('--'):
                        continue
                    lines.append(line)
                statement = ' '.join(lines).strip()
                if not statement:
                    continue
                try:
                    logger.debug(f"执行建表 SQL: {statement}")
                    await cursor.execute(statement)
                except Exception as e:
                    msg = str(e).lower()
                    if "already exists" in msg:
                        # 目标是幂等初始化，已存在时仅记录调试日志
                        logger.debug(f"表已存在，跳过语句: {e}")
                    else:
                        logger.error(f"执行建表 SQL 失败: {e}；语句：{statement}")
                        raise
            
            # 执行初始数据
            for raw in INIT_DATA_SQL.split(';'):
                lines = []
                for line in raw.splitlines():
                    if line.strip().startswith('--'):
                        continue
                    lines.append(line)
                statement = ' '.join(lines).strip()
                if not statement:
                    continue
                try:
                    await cursor.execute(statement)
                except Exception as e:
                    logger.debug(f"初始数据可能已存在: {e}")
            
            # 校验核心表是否已创建成功，避免“脚本成功但表缺失”的情况
            required_tables = [
                "project",
                "project_node",
                "node_type",
                "function_document",
                "dictionary",
                "document_content",
                "document_block",
            ]
            await cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name IN (%s)
                """ % (
                    "%s",
                    ",".join(["%s"] * len(required_tables)),
                ),
                (settings.db_name, *required_tables),
            )
            existing = {row[0] for row in await cursor.fetchall()}
            missing = [t for t in required_tables if t not in existing]
            if missing:
                # 直接抛错，让调用方感知初始化失败
                raise RuntimeError(f"以下表创建失败或不存在: {', '.join(missing)}")

            # 迁移：为已存在的 project_node 表添加 document_id 列
            try:
                await cursor.execute(
                    "ALTER TABLE project_node ADD COLUMN document_id BIGINT DEFAULT NULL "
                    "COMMENT '功能节点关联的文档 ID' AFTER status"
                )
                logger.info("已为 project_node 表添加 document_id 列")
            except Exception as e:
                if "Duplicate column" in str(e):
                    logger.debug("project_node.document_id 列已存在，跳过")
                elif "doesn't exist" in str(e) or "does not exist" in str(e):
                    # 新环境下 project_node 本身刚按最新结构创建，不需要额外迁移
                    logger.debug("project_node 表不存在或刚按最新结构创建，跳过迁移: %s", e)
                else:
                    logger.warning(f"添加 document_id 列时出错: {e}")
        
        await connection.commit()
        logger.info("✓ MariaDB 数据库初始化完成")
        
    except Exception as e:
        logger.error(f"MariaDB 初始化失败: {e}", exc_info=True)
        raise
    finally:
        if connection:
            connection.close()


async def main():
    """主函数。"""
    logger.info("=" * 50)
    logger.info("DIP Studio 数据库初始化")
    logger.info("=" * 50)
    
    settings = get_settings()
    
    try:
        # 初始化 MariaDB（含文档内容、文档块表）
        await init_mariadb(settings)
        
        logger.info("=" * 50)
        logger.info("数据库初始化完成！")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
