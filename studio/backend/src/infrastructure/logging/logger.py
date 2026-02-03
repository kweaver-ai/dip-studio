"""
日志配置模块

提供统一的日志配置。
"""
import logging
import sys
from typing import Optional

from src.infrastructure.config.settings import Settings


def setup_logging(settings: Optional[Settings] = None) -> logging.Logger:
    """
    配置应用日志。
    
    参数:
        settings: 应用配置。如果为 None，则使用默认配置。
    
    返回:
        logging.Logger: 配置完成的根日志记录器。
    """
    if settings is None:
        from src.infrastructure.config.settings import get_settings
        settings = get_settings()
    
    # 获取日志级别
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 移除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 设置日志格式
    formatter = logging.Formatter(settings.log_format)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到根日志记录器
    root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
    logging.getLogger("uvicorn.error").setLevel(log_level)
    
    # 降低一些第三方库的日志级别
    logging.getLogger("aiomysql").setLevel(logging.WARNING)
    
    return root_logger
