"""
内部接口路由（无认证，供 MCP Server 等调用）

路径包含 /internal/ 时认证中间件会放行。
"""
import logging

from fastapi import APIRouter, Path

from src.application.node_service import NodeService
from src.infrastructure.exceptions import NotFoundError, InternalError

logger = logging.getLogger(__name__)


def create_internal_router(node_service: NodeService) -> APIRouter:
    """
    创建内部接口路由。

    参数:
        node_service: 节点服务实例

    返回:
        APIRouter: 配置完成的路由
    """
    router = APIRouter(tags=["Internal"])

    @router.get(
        "/nodes/{node_id}/application-detail",
        summary="获取应用详情（MCP）",
        description="根据节点 ID 返回待开发内容（该节点及子节点含文档）与背景 Context（该节点父节点链至根节点）。每项含 document（TipTap 原始 JSON）与 document_text（可读文本，供 Coding Agent 使用）。内部接口，无需认证。",
        responses={
            200: {"description": "成功"},
            404: {"description": "节点不存在"},
        },
    )
    async def get_application_detail(
        node_id: str = Path(..., description="节点 ID (UUID)（URL 所代表的节点）"),
    ) -> dict:
        """供 MCP Server 获取应用详情。"""
        try:
            return await node_service.get_application_detail_for_mcp(node_id)
        except ValueError as e:
            if "不存在" in str(e):
                raise NotFoundError(description=str(e))
            raise
        except Exception as e:
            logger.exception(f"获取应用详情失败: {e}")
            raise InternalError(description=f"获取应用详情失败: {str(e)}")

    return router
