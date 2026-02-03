"""
MariaDB 数据库连接管理

提供 MariaDB 数据库连接池管理。
"""
import logging
from typing import Optional

import aiomysql

from src.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class MariaDBPool:
    """
    MariaDB 连接池管理器。
    """
    
    def __init__(self, settings: Settings):
        """
        初始化连接池管理器。
        
        参数:
            settings: 应用配置
        """
        self._settings = settings
        self._pool: Optional[aiomysql.Pool] = None
    
    async def get_pool(self) -> aiomysql.Pool:
        """
        获取数据库连接池。
        
        返回:
            aiomysql.Pool: 数据库连接池
        """
        if self._pool is None:
            self._pool = await aiomysql.create_pool(
                host=self._settings.db_host,
                port=self._settings.db_port,
                user=self._settings.db_user,
                password=self._settings.db_password,
                db=self._settings.db_name,
                autocommit=True,
                minsize=self._settings.db_pool_min_size,
                maxsize=self._settings.db_pool_max_size,
                charset='utf8mb4',
            )
            logger.info(
                f"MariaDB 连接池已创建: "
                f"{self._settings.db_host}:{self._settings.db_port}/{self._settings.db_name}"
            )
        return self._pool
    
    async def close(self) -> None:
        """关闭数据库连接池。"""
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
            logger.info("MariaDB 连接池已关闭")
