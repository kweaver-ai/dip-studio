"""
功能设计文档路由

适配前端 TipTap + fast-json-patch 方案，提供 2 个接口：
- 文档查询：入参 document_id，返回完整文档 JSON（单对象 {}，创建功能节点时已初始化为空 {}）
- 文档增量：PUT 请求体为 JSON Patch 操作数组，仅返回是否更新成功
"""
import logging

from fastapi import APIRouter, Body, Path

from src.application.document_service import DocumentService
from src.infrastructure.exceptions import NotFoundError, ValidationError, InternalError
from src.routers.schemas.document import PatchDocumentResponse
from src.routers.schemas.project import ErrorResponse

logger = logging.getLogger(__name__)


def create_document_router(document_service: DocumentService) -> APIRouter:
    """
    创建文档路由（2 个接口：查询、增量更新；创建功能节点时已自动初始化文档为空 {}）。

    参数:
        document_service: 文档服务实例

    返回:
        APIRouter: 配置完成的路由
    """
    router = APIRouter(prefix="/documents", tags=["Document"])

    # 1. 文档查询：入参 document_id，返回完整文档 JSON（单对象 {}）
    @router.get(
        "/{document_id}",
        summary="查询文档",
        description="入参 document_id（创建功能节点时已生成并初始化为空 {}），返回完整文档 JSON（单对象 {}）。",
        responses={
            200: {"description": "查询成功", "content": {"application/json": {"schema": {"type": "object", "description": "文档内容对象 {}"}}}},
            404: {"description": "文档不存在", "model": ErrorResponse},
        }
    )
    async def get_document(
        document_id: int = Path(..., description="文档 ID", ge=1),
    ) -> dict:
        """根据 document_id 获取完整文档 JSON（单对象 {}）。"""
        try:
            return await document_service.get_document_content(document_id)
        except ValueError as e:
            if "不存在" in str(e):
                raise NotFoundError(description=str(e))
            raise ValidationError(
                code="INVALID_REQUEST",
                description=str(e),
                solution="请检查 document_id",
            )
        except Exception as e:
            logger.exception(f"查询文档失败: {e}")
            raise InternalError(description=f"查询文档失败: {str(e)}")

    # 2. 文档增量：PUT 请求体为 JSON Patch 操作数组，仅返回是否更新成功
    @router.put(
        "/{document_id}",
        summary="文档增量更新",
        description="对文档内容 {} 进行增量更新（RFC 6902 JSON Patch），仅返回是否更新成功。",
        response_model=PatchDocumentResponse,
        responses={
            200: {"description": "更新成功"},
            400: {"description": "请求参数错误或 Patch 无效", "model": ErrorResponse},
            404: {"description": "文档不存在", "model": ErrorResponse},
        }
    )
    async def put_document(
        patch_operations: list[dict] = Body(..., description="RFC 6902 JSON Patch 操作数组"),
        document_id: int = Path(..., description="文档 ID", ge=1),
    ) -> PatchDocumentResponse:
        """文档增量更新（PUT），仅返回是否更新成功。"""
        try:
            await document_service.patch_document_content(
                document_id=document_id,
                patch_operations=patch_operations,
            )
            return PatchDocumentResponse(success=True)
        except ValueError as e:
            error_msg = str(e)
            if "不存在" in error_msg:
                raise NotFoundError(description=error_msg)
            raise ValidationError(
                code="INVALID_REQUEST",
                description=error_msg,
                solution="请检查 Patch 格式与 path",
            )
        except Exception as e:
            logger.exception(f"文档增量更新失败: {e}")
            raise InternalError(description=f"文档增量更新失败: {str(e)}")

    return router
