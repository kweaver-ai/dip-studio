"""
节点路由

节点管理端点的 FastAPI 路由。
"""
import logging
from typing import Optional

from fastapi import APIRouter, Path, Query, status
from fastapi.responses import Response

from src.application.node_service import NodeService
from src.infrastructure.exceptions import NotFoundError, ValidationError, InternalError
from src.infrastructure.context import get_user_id
from src.routers.schemas.node import (
    CreateApplicationNodeRequest,
    CreatePageNodeRequest,
    CreateFunctionNodeRequest,
    UpdateNodeRequest,
    MoveNodeRequest,
    NodeResponse,
    NodeTreeResponse,
)
from src.routers.schemas.project import ErrorResponse

logger = logging.getLogger(__name__)


def create_node_router(node_service: NodeService) -> APIRouter:
    """
    创建节点路由。

    参数:
        node_service: 节点服务实例

    返回:
        APIRouter: 配置完成的路由
    """
    router = APIRouter(prefix="/nodes", tags=["Node"])

    def _node_to_response(node) -> NodeResponse:
        """将节点领域模型转换为响应模型。"""
        return NodeResponse(
            id=node.id,
            project_id=node.project_id,
            parent_id=node.parent_id,
            node_type=node.node_type.value,
            name=node.name,
            description=node.description,
            path=node.path,
            sort=node.sort,
            status=node.status,
            document_id=node.document_id,
            creator=node.creator,
            created_at=node.created_at,
            editor=node.editor,
            edited_at=node.edited_at,
        )

    def _node_to_tree_response(node) -> NodeTreeResponse:
        """将节点领域模型转换为树响应模型（不含 sort，children 已按 sort 顺序）。"""
        return NodeTreeResponse(
            id=node.id,
            project_id=node.project_id,
            parent_id=node.parent_id,
            node_type=node.node_type.value,
            name=node.name,
            description=node.description,
            path=node.path,
            status=node.status,
            document_id=node.document_id,
            creator=node.creator,
            created_at=node.created_at,
            editor=node.editor,
            edited_at=node.edited_at,
            children=[_node_to_tree_response(child) for child in node.children],
        )

    @router.post(
        "/application",
        summary="创建应用节点",
        description="创建应用节点（根节点），一个项目只能有一个",
        response_model=NodeResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            201: {"description": "创建成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
        }
    )
    async def create_application_node(
        request: CreateApplicationNodeRequest,
    ) -> NodeResponse:
        """创建应用节点。"""
        try:
            node = await node_service.create_application_node(
                project_id=request.project_id,
                name=request.name,
                description=request.description,
                creator=get_user_id(),
            )
            return _node_to_response(node)
        except ValueError as e:
            raise ValidationError(
                code="INVALID_REQUEST",
                description=str(e),
                solution="请检查请求参数",
            )
        except Exception as e:
            logger.exception(f"创建应用节点失败: {e}")
            raise InternalError(description=f"创建应用节点失败: {str(e)}")

    @router.post(
        "/page",
        summary="创建页面节点",
        description="创建页面节点，只能在应用节点下创建",
        response_model=NodeResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            201: {"description": "创建成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
        }
    )
    async def create_page_node(
        request: CreatePageNodeRequest,
    ) -> NodeResponse:
        """创建页面节点。"""
        try:
            node = await node_service.create_page_node(
                project_id=request.project_id,
                parent_id=request.parent_id,
                name=request.name,
                description=request.description,
                creator=get_user_id(),
            )
            return _node_to_response(node)
        except ValueError as e:
            raise ValidationError(
                code="INVALID_REQUEST",
                description=str(e),
                solution="请检查请求参数",
            )
        except Exception as e:
            logger.exception(f"创建页面节点失败: {e}")
            raise InternalError(description=f"创建页面节点失败: {str(e)}")

    @router.post(
        "/function",
        summary="创建功能节点",
        description="创建功能节点，只能在页面节点下创建，会自动创建关联的功能设计文档",
        response_model=NodeResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            201: {"description": "创建成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
        }
    )
    async def create_function_node(
        request: CreateFunctionNodeRequest,
    ) -> NodeResponse:
        """创建功能节点。"""
        try:
            node = await node_service.create_function_node(
                project_id=request.project_id,
                parent_id=request.parent_id,
                name=request.name,
                description=request.description,
                creator=get_user_id(),
            )
            return _node_to_response(node)
        except ValueError as e:
            raise ValidationError(
                code="INVALID_REQUEST",
                description=str(e),
                solution="请检查请求参数",
            )
        except Exception as e:
            logger.exception(f"创建功能节点失败: {e}")
            raise InternalError(description=f"创建功能节点失败: {str(e)}")

    @router.put(
        "/{node_id}",
        summary="更新节点",
        description="更新节点信息",
        response_model=NodeResponse,
        responses={
            200: {"description": "更新成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
            404: {"description": "节点不存在", "model": ErrorResponse},
        }
    )
    async def update_node(
        request: UpdateNodeRequest,
        node_id: int = Path(..., description="节点 ID", ge=1),
    ) -> NodeResponse:
        """更新节点。"""
        try:
            node = await node_service.update_node(
                node_id=node_id,
                name=request.name,
                description=request.description,
                editor=get_user_id(),
            )
            return _node_to_response(node)
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
            logger.exception(f"更新节点失败: {e}")
            raise InternalError(description=f"更新节点失败: {str(e)}")

    @router.put(
        "/move",
        summary="移动节点",
        description="移动节点到新的父节点下",
        response_model=NodeResponse,
        responses={
            200: {"description": "移动成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
            404: {"description": "节点不存在", "model": ErrorResponse},
        }
    )
    async def move_node(request: MoveNodeRequest) -> NodeResponse:
        """移动节点。"""
        try:
            node = await node_service.move_node(
                node_id=request.node_id,
                new_parent_id=request.new_parent_id,
                predecessor_node_id=request.predecessor_node_id,
                editor=get_user_id(),
            )
            return _node_to_response(node)
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
            logger.exception(f"移动节点失败: {e}")
            raise InternalError(description=f"移动节点失败: {str(e)}")

    @router.delete(
        "/{node_id}",
        summary="删除节点",
        description="删除节点（节点不能有子节点）",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            204: {"description": "删除成功"},
            400: {"description": "请求参数错误", "model": ErrorResponse},
            404: {"description": "节点不存在", "model": ErrorResponse},
        }
    )
    async def delete_node(
        node_id: int = Path(..., description="节点 ID", ge=1),
    ) -> Response:
        """删除节点。"""
        try:
            await node_service.delete_node(node_id)
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
            logger.exception(f"删除节点失败: {e}")
            raise InternalError(description=f"删除节点失败: {str(e)}")

    return router


def create_project_nodes_router(node_service: NodeService) -> APIRouter:
    """
    创建项目节点路由（用于获取节点树）。

    参数:
        node_service: 节点服务实例

    返回:
        APIRouter: 配置完成的路由
    """
    router = APIRouter(prefix="/projects", tags=["Node"])

    def _node_to_tree_response(node) -> NodeTreeResponse:
        """将节点领域模型转换为树响应模型（不含 sort，children 已按 sort 顺序）。"""
        return NodeTreeResponse(
            id=node.id,
            project_id=node.project_id,
            parent_id=node.parent_id,
            node_type=node.node_type.value,
            name=node.name,
            description=node.description,
            path=node.path,
            status=node.status,
            document_id=node.document_id,
            creator=node.creator,
            created_at=node.created_at,
            editor=node.editor,
            edited_at=node.edited_at,
            children=[_node_to_tree_response(child) for child in node.children],
        )

    @router.get(
        "/{project_id}/nodes/tree",
        summary="获取节点树",
        description="获取项目的完整节点树",
        response_model=Optional[NodeTreeResponse],
        responses={
            200: {"description": "获取成功"},
            404: {"description": "项目不存在", "model": ErrorResponse},
        }
    )
    async def get_node_tree(
        project_id: int = Path(..., description="项目 ID", ge=1),
    ) -> Optional[NodeTreeResponse]:
        """获取节点树。"""
        try:
            root = await node_service.get_node_tree(project_id)
            if root is None:
                return None
            return _node_to_tree_response(root)
        except Exception as e:
            logger.exception(f"获取节点树失败: {e}")
            raise InternalError(description=f"获取节点树失败: {str(e)}")

    return router
