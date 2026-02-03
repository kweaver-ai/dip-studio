"""
健康检查路由

健康检查端点的 FastAPI 路由。
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """健康检查响应。"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="服务版本")


def create_health_router(version: str = "0.1.0") -> APIRouter:
    """
    创建健康检查路由。

    参数:
        version: 服务版本

    返回:
        APIRouter: 配置完成的路由
    """
    router = APIRouter(tags=["Health"])

    @router.get(
        "/health",
        summary="健康检查",
        description="检查服务健康状态",
        response_model=HealthResponse,
    )
    async def health_check() -> HealthResponse:
        """健康检查。"""
        return HealthResponse(
            status="healthy",
            version=version,
        )

    @router.get(
        "/ready",
        summary="就绪检查",
        description="检查服务是否就绪",
        response_model=HealthResponse,
    )
    async def ready_check() -> HealthResponse:
        """就绪检查。"""
        return HealthResponse(
            status="ready",
            version=version,
        )

    return router
