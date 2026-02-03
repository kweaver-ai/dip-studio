"""
项目词典路由

项目词典管理端点的 FastAPI 路由。
"""
import logging
from typing import List

from fastapi import APIRouter, Path, Query, status
from fastapi.responses import Response

from src.application.dictionary_service import DictionaryService
from src.infrastructure.exceptions import NotFoundError, ValidationError, ConflictError, InternalError
from src.routers.schemas.dictionary import (
    CreateDictionaryEntryRequest,
    UpdateDictionaryEntryRequest,
    DictionaryEntryResponse,
)
from src.routers.schemas.project import ErrorResponse

logger = logging.getLogger(__name__)


def create_dictionary_router(dictionary_service: DictionaryService) -> APIRouter:
    """
    创建词典路由。

    参数:
        dictionary_service: 词典服务实例

    返回:
        APIRouter: 配置完成的路由
    """
    router = APIRouter(prefix="/dictionary", tags=["Dictionary"])

    def _entry_to_response(entry) -> DictionaryEntryResponse:
        """将词典条目领域模型转换为响应模型。"""
        return DictionaryEntryResponse(
            id=entry.id,
            project_id=entry.project_id,
            term=entry.term,
            definition=entry.definition,
            created_at=entry.created_at,
        )

    @router.post(
        "",
        summary="新增术语",
        description="新增项目词典术语",
        response_model=DictionaryEntryResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            201: {"description": "创建成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
            409: {"description": "术语已存在", "model": ErrorResponse},
        }
    )
    async def create_entry(request: CreateDictionaryEntryRequest) -> DictionaryEntryResponse:
        """新增术语。"""
        try:
            entry = await dictionary_service.create_entry(
                project_id=request.project_id,
                term=request.term,
                definition=request.definition,
            )
            return _entry_to_response(entry)
        except ValueError as e:
            error_msg = str(e)
            if "已存在" in error_msg:
                raise ConflictError(
                    code="TERM_EXISTS",
                    description=error_msg,
                    solution="一个术语在项目中只能定义一次",
                )
            raise ValidationError(
                code="INVALID_REQUEST",
                description=error_msg,
                solution="请检查请求参数",
            )
        except Exception as e:
            logger.exception(f"创建词典条目失败: {e}")
            raise InternalError(description=f"创建词典条目失败: {str(e)}")

    @router.get(
        "",
        summary="查询词典",
        description="查询项目的所有词典条目",
        response_model=List[DictionaryEntryResponse],
    )
    async def get_entries(
        project_id: int = Query(..., description="项目 ID", ge=1),
    ) -> List[DictionaryEntryResponse]:
        """查询词典。"""
        try:
            entries = await dictionary_service.get_entries_by_project_id(project_id)
            return [_entry_to_response(e) for e in entries]
        except Exception as e:
            logger.exception(f"查询词典失败: {e}")
            raise InternalError(description=f"查询词典失败: {str(e)}")

    @router.put(
        "/{entry_id}",
        summary="更新术语",
        description="更新词典术语",
        response_model=DictionaryEntryResponse,
        responses={
            200: {"description": "更新成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
            404: {"description": "条目不存在", "model": ErrorResponse},
            409: {"description": "术语已存在", "model": ErrorResponse},
        }
    )
    async def update_entry(
        request: UpdateDictionaryEntryRequest,
        entry_id: int = Path(..., description="条目 ID", ge=1),
    ) -> DictionaryEntryResponse:
        """更新术语。"""
        try:
            entry = await dictionary_service.update_entry(
                entry_id=entry_id,
                term=request.term,
                definition=request.definition,
            )
            return _entry_to_response(entry)
        except ValueError as e:
            error_msg = str(e)
            if "不存在" in error_msg:
                raise NotFoundError(description=error_msg)
            if "已存在" in error_msg:
                raise ConflictError(
                    code="TERM_EXISTS",
                    description=error_msg,
                    solution="一个术语在项目中只能定义一次",
                )
            raise ValidationError(
                code="INVALID_REQUEST",
                description=error_msg,
                solution="请检查请求参数",
            )
        except Exception as e:
            logger.exception(f"更新词典条目失败: {e}")
            raise InternalError(description=f"更新词典条目失败: {str(e)}")

    @router.delete(
        "/{entry_id}",
        summary="删除术语",
        description="删除词典术语",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            204: {"description": "删除成功"},
            404: {"description": "条目不存在", "model": ErrorResponse},
        }
    )
    async def delete_entry(
        entry_id: int = Path(..., description="条目 ID", ge=1),
    ) -> Response:
        """删除术语。"""
        try:
            await dictionary_service.delete_entry(entry_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            raise NotFoundError(description=str(e))
        except Exception as e:
            logger.exception(f"删除词典条目失败: {e}")
            raise InternalError(description=f"删除词典条目失败: {str(e)}")

    return router
