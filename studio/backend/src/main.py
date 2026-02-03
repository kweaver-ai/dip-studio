"""
DIP Studio 应用程序入口

这是 FastAPI 应用程序的主入口点。
负责组装依赖（注入适配器实现）并启动 Web 服务。
"""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 将项目根目录添加到 Python 路径，以便模块导入
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.infrastructure.config.settings import get_settings, Settings
from src.infrastructure.exceptions import BusinessException, create_error_response
from src.infrastructure.container import init_container, get_container
from src.infrastructure.logging.logger import setup_logging
from src.infrastructure.middleware.auth_middleware import AuthMiddleware
from src.routers.health_router import create_health_router
from src.routers.project_router import create_project_router
from src.routers.node_router import create_node_router, create_project_nodes_router
from src.routers.dictionary_router import create_dictionary_router
from src.routers.document_router import create_document_router
from src.routers.internal_router import create_internal_router


def create_app(settings: Settings = None) -> FastAPI:
    """
    创建并配置 FastAPI 应用程序。
    
    参数:
        settings: 应用配置。如果为 None，则使用默认配置。
    
    返回:
        FastAPI: 配置完成的应用实例。
    """
    if settings is None:
        settings = get_settings()
    
    # 设置日志
    logger = setup_logging(settings)
    
    # 初始化依赖注入容器
    container = init_container(settings)
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """应用生命周期管理器。"""
        logger.info(f"启动 {settings.app_name} v{settings.app_version}")
        logger.info(f"服务运行在 {settings.host}:{settings.port}")

        # 初始化完成后标记服务为就绪状态
        container.set_ready(True)
        logger.info("服务已准备好接受请求")

        yield

        # 关闭时清理资源
        logger.info("正在关闭服务")
        container.set_ready(False)

        # 关闭数据库连接池
        await container.close()
        logger.info("资源已释放")
    
    # 创建 FastAPI 应用
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )
    
    # 添加认证中间件
    app.add_middleware(AuthMiddleware)
    
    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册全局异常处理器
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        """处理业务异常，返回统一格式的错误响应。"""
        return exc.to_response()
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求参数验证异常。"""
        errors = exc.errors()
        detail = {"validation_errors": errors} if errors else None
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="VALIDATION_ERROR",
            description="请求参数验证失败",
            solution="请检查请求参数格式是否正确",
            detail=detail,
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """处理未捕获的异常。"""
        logger.exception(f"未捕获的异常: {exc}")
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
            description="服务器内部错误",
            solution="请稍后重试或联系管理员",
        )
    
    # 注册路由
    # 健康检查
    health_router = create_health_router(settings.app_version)
    app.include_router(health_router, prefix=settings.api_prefix)
    
    # 项目管理
    project_router = create_project_router(container.project_service)
    app.include_router(project_router, prefix=settings.api_prefix)
    
    # 节点管理
    node_router = create_node_router(container.node_service)
    app.include_router(node_router, prefix=settings.api_prefix)
    
    # 项目节点树（单独的路由前缀）
    project_nodes_router = create_project_nodes_router(container.node_service)
    app.include_router(project_nodes_router, prefix=settings.api_prefix)
    
    # 项目词典
    dictionary_router = create_dictionary_router(container.dictionary_service)
    app.include_router(dictionary_router, prefix=settings.api_prefix)
    
    # 功能设计文档（TipTap + fast-json-patch：查询 / 初始化 / 增量）
    document_router = create_document_router(container.document_service)
    app.include_router(document_router, prefix=settings.api_prefix)

    # 内部接口（无认证，供 MCP Server 等调用）路径：/internal/api/dip-studio/v1/...
    internal_router = create_internal_router(container.node_service)
    app.include_router(internal_router, prefix=f"/internal{settings.api_prefix}")

    return app


# 创建应用实例
app = create_app()


def main():
    """使用 uvicorn 运行应用程序。"""
    settings = get_settings()
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
