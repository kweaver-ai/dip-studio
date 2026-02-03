"""
应用配置管理

使用 pydantic-settings 进行配置管理。
配置可以通过环境变量或 .env 文件进行设置。
"""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置。
    
    所有配置都可以通过环境变量进行设置。
    环境变量需要以 'DIP_STUDIO_' 为前缀。
    """
    
    model_config = SettingsConfigDict(
        env_prefix="DIP_STUDIO_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # 应用配置
    app_name: str = Field(default="DIP Studio", description="应用名称")
    app_version: str = Field(default="0.1.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8000, description="服务器监听端口")
    workers: int = Field(default=1, description="工作进程数")
    
    # API 配置
    api_prefix: str = Field(default="/api/dip-studio/v1", description="API 前缀")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
    # MariaDB 配置
    db_host: str = Field(default="localhost", description="MariaDB 主机")
    db_port: int = Field(default=3306, description="MariaDB 端口")
    db_name: str = Field(default="dip_studio", description="MariaDB 数据库名称")
    db_user: str = Field(default="root", description="MariaDB 用户名")
    db_password: str = Field(default="", description="MariaDB 密码")
    db_pool_min_size: int = Field(default=1, description="连接池最小连接数")
    db_pool_max_size: int = Field(default=10, description="连接池最大连接数")
    
    # Mock 模式配置
    use_mock_services: bool = Field(
        default=False, 
        description="是否使用 Mock 外部服务（用于本地开发调试）"
    )
    
    # 临时文件配置
    temp_dir: str = Field(default="/tmp/dip-studio", description="临时文件目录")


@lru_cache
def get_settings() -> Settings:
    """
    获取缓存的配置实例。
    
    返回:
        Settings: 应用配置。
    """
    return Settings()
