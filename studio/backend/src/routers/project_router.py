"""
项目路由

项目管理端点的 FastAPI 路由。
"""
import logging
from typing import List

from fastapi import APIRouter, Path, status
from starlette.responses import Response

from src.application.project_service import ProjectService
from src.infrastructure.exceptions import NotFoundError, ValidationError, ConflictError, InternalError
from src.infrastructure.context import get_user_id, get_user_name
from src.routers.schemas.project import (
    CreateProjectRequest,
    UpdateProjectRequest,
    ProjectResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)


def create_project_router(project_service: ProjectService) -> APIRouter:
    """
    创建项目路由。

    参数:
        project_service: 项目服务实例

    返回:
        APIRouter: 配置完成的路由
    """
    router = APIRouter(prefix="/projects", tags=["Project"])

    def _project_to_response(project) -> ProjectResponse:
        """将项目领域模型转换为响应模型。"""
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            creator_id=project.creator_id,
            creator_name=project.creator_name,
            created_at=project.created_at,
            editor_id=project.editor_id,
            editor_name=project.editor_name,
            edited_at=project.edited_at,
        )

    @router.post(
        "",
        summary="创建项目",
        description="创建新的项目",
        response_model=ProjectResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            201: {"description": "创建成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
            409: {"description": "项目名称已存在", "model": ErrorResponse},
        }
    )
    async def create_project(request: CreateProjectRequest) -> ProjectResponse:
        """创建项目。"""
        try:
            project = await project_service.create_project(
                name=request.name,
                description=request.description,
                creator_id=get_user_id(),
                creator_name=get_user_name(),
            )
            return _project_to_response(project)
        except ValueError as e:
            error_msg = str(e)
            if "已存在" in error_msg:
                raise ConflictError(
                    code="PROJECT_NAME_EXISTS",
                    description=error_msg,
                    solution="请使用不同的项目名称",
                )
            raise ValidationError(
                code="INVALID_REQUEST",
                description=error_msg,
                solution="请检查请求参数",
            )
        except Exception as e:
            logger.exception(f"创建项目失败: {e}")
            raise InternalError(description=f"创建项目失败: {str(e)}")

    @router.get(
        "",
        summary="获取项目列表",
        description="获取所有项目列表",
        response_model=List[ProjectResponse],
    )
    async def get_projects() -> List[ProjectResponse]:
        """获取项目列表（仅返回当前用户创建的项目，当前用户由上下文决定）。"""
        try:
            projects = await project_service.get_all_projects()
            return [_project_to_response(p) for p in projects]
        except Exception as e:
            logger.exception(f"获取项目列表失败: {e}")
            raise InternalError(description=f"获取项目列表失败: {str(e)}")

    @router.get(
        "/{project_id}",
        summary="获取项目详情",
        description="根据项目 ID 获取项目详情",
        response_model=ProjectResponse,
        responses={
            200: {"description": "获取成功"},
            404: {"description": "项目不存在", "model": ErrorResponse},
        }
    )
    async def get_project(
        project_id: int = Path(..., description="项目 ID", ge=1),
    ) -> ProjectResponse:
        """获取项目详情。"""
        try:
            project = await project_service.get_project_by_id(project_id)
            return _project_to_response(project)
        except ValueError as e:
            raise NotFoundError(description=str(e))
        except Exception as e:
            logger.exception(f"获取项目失败: {e}")
            raise InternalError(description=f"获取项目失败: {str(e)}")

    @router.put(
        "/{project_id}",
        summary="更新项目",
        description="更新项目信息",
        response_model=ProjectResponse,
        responses={
            200: {"description": "更新成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
            404: {"description": "项目不存在", "model": ErrorResponse},
            409: {"description": "项目名称已存在", "model": ErrorResponse},
        }
    )
    async def update_project(
        request: UpdateProjectRequest,
        project_id: int = Path(..., description="项目 ID", ge=1),
    ) -> ProjectResponse:
        """更新项目。"""
        try:
            project = await project_service.update_project(
                project_id=project_id,
                name=request.name,
                description=request.description,
                editor_id=get_user_id(),
                editor_name=get_user_name(),
            )
            return _project_to_response(project)
        except ValueError as e:
            error_msg = str(e)
            if "不存在" in error_msg:
                raise NotFoundError(description=error_msg)
            if "已存在" in error_msg:
                raise ConflictError(
                    code="PROJECT_NAME_EXISTS",
                    description=error_msg,
                    solution="请使用不同的项目名称",
                )
            raise ValidationError(
                code="INVALID_REQUEST",
                description=error_msg,
                solution="请检查请求参数",
            )
        except Exception as e:
            logger.exception(f"更新项目失败: {e}")
            raise InternalError(description=f"更新项目失败: {str(e)}")

    @router.delete(
        "/{project_id}",
        summary="删除项目",
        description="删除项目。确认操作由前端完成。",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            204: {"description": "删除成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
            404: {"description": "项目不存在", "model": ErrorResponse},
        }
    )
    async def delete_project(
        project_id: int = Path(..., description="项目 ID", ge=1),
    ) -> Response:
        """删除项目。"""
        try:
            await project_service.delete_project(project_id=project_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            error_msg = str(e)
            if "不存在" in error_msg:
                raise NotFoundError(description=error_msg)
            raise ValidationError(
                code="INVALID_REQUEST",
                description=error_msg,
                solution="请检查请求参数",
            )
        except Exception as e:
            logger.exception(f"删除项目失败: {e}")
            raise InternalError(description=f"删除项目失败: {str(e)}")

    return router
