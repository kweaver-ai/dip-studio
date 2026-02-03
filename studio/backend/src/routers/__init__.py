"""
路由模块

定义 API 路由端点。
"""
from src.routers.project_router import create_project_router
from src.routers.node_router import create_node_router
from src.routers.dictionary_router import create_dictionary_router
from src.routers.document_router import create_document_router
from src.routers.health_router import create_health_router

__all__ = [
    "create_project_router",
    "create_node_router",
    "create_dictionary_router",
    "create_document_router",
    "create_health_router",
]
