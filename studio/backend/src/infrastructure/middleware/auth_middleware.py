"""
认证中间件

统一从请求头提取认证token并存储到request.state和TokenContext中，供后续处理使用。
同时进行token内省并获取用户信息，存储到上下文中。
与 hub 实现一致：通过 Hydra 内省获取用户 ID，再通过用户管理服务获取用户详情。
对于需要认证的路径，如果没有token则拒绝访问。
"""
import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.infrastructure.context.token_context import TokenContext, UserContext
from src.infrastructure.container import get_container
from src.infrastructure.exceptions import UnauthorizedError
from src.ports.user_management_port import UserInfo

logger = logging.getLogger(__name__)

# 不需要认证的路径前缀列表
PUBLIC_PATHS = [
    "/health",
    "/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
]

# 内部接口路径前缀（不需要认证）
INTERNAL_PATHS = [
    "/internal/",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件。

    从请求头中提取 Authorization token，进行内省验证，并存储到：
    1. request.state.auth_token - 供路由层使用
    2. TokenContext - 供适配器层统一获取
    3. UserContext - 供应用层统一获取用户信息（由 Hydra 内省 + 用户管理服务获取）

    对于需要认证的路径，如果没有 token 或 token 无效则拒绝访问。
    """

    def _is_public_path(self, path: str) -> bool:
        """
        判断路径是否为公开路径（不需要认证）。

        参数:
            path: 请求路径

        返回:
            bool: 如果是公开路径返回True，否则返回False
        """
        # 检查是否为内部接口
        for internal_path in INTERNAL_PATHS:
            if internal_path in path:
                return True

        # 检查路径是否以公开路径前缀开头
        for public_path in PUBLIC_PATHS:
            if path == public_path:
                return True
            if path.endswith(public_path) or path.endswith(public_path + "/"):
                return True
            if path.startswith(public_path + "/") or path.startswith(public_path + "?"):
                return True
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        处理请求，提取认证 token，进行内省并获取用户信息。
        """
        path = request.url.path

        if self._is_public_path(path):
            try:
                response = await call_next(request)
                return response
            finally:
                TokenContext.clear_token()
                UserContext.clear_user_info()

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(f"请求路径 {path} 需要认证，但未提供token")
            error = UnauthorizedError(
                description="访问此资源需要认证",
                solution="请在请求头中提供有效的Authorization token",
            )
            return error.to_response()

        if auth_header.startswith("Bearer "):
            auth_token = auth_header[7:]
        else:
            auth_token = auth_header

        if not auth_token:
            logger.warning(f"请求路径 {path} 需要认证，但token为空")
            error = UnauthorizedError(
                description="访问此资源需要认证",
                solution="请在请求头中提供有效的Authorization token",
            )
            return error.to_response()

        request.state.auth_token = auth_header
        TokenContext.set_token(auth_token)

        # 与 hub 一致：内省 token 获取用户 ID，再通过用户管理服务获取用户信息
        user_info = None
        try:
            container = get_container()
            introspect = await container.hydra_adapter.introspect(auth_token)
            if introspect.active and introspect.visitor_id:
                user_infos = await container.user_management_adapter.batch_get_user_info_by_id(
                    [introspect.visitor_id]
                )
                if introspect.visitor_id in user_infos:
                    user_info = user_infos[introspect.visitor_id]
                    logger.debug(f"用户信息已获取: {user_info.id} ({user_info.vision_name})")
                else:
                    logger.warning(f"无法获取用户信息: {introspect.visitor_id}")
                    error = UnauthorizedError(
                        description="无法获取用户信息",
                        solution="请使用有效的token重新登录",
                    )
                    return error.to_response()
            else:
                logger.warning("Token 内省结果：token 无效或无法获取用户ID")
                error = UnauthorizedError(
                    description="Token无效或已过期",
                    solution="请使用有效的token重新登录",
                )
                return error.to_response()
        except Exception as e:
            logger.error(f"Token 内省或获取用户信息失败: {e}", exc_info=True)
            error = UnauthorizedError(
                description="Token验证失败",
                solution="请使用有效的token重新登录",
            )
            return error.to_response()

        UserContext.set_user_info(user_info)
        request.state.user_id = user_info.id
        request.state.user_info = user_info

        try:
            response = await call_next(request)
            return response
        finally:
            TokenContext.clear_token()
            UserContext.clear_user_info()


def get_auth_token_from_request(request: Request) -> Optional[str]:
    """
    从请求中获取认证Token。
    
    参数:
        request: HTTP请求
    
    返回:
        Optional[str]: 认证Token，不存在时返回None
    """
    return getattr(request.state, "auth_token", None)


def get_user_id_from_request(request: Request) -> str:
    """
    从请求中获取用户ID（UUID 字符串）。

    参数:
        request: HTTP请求

    返回:
        str: 用户ID，不存在时返回空字符串
    """
    return getattr(request.state, "user_id", "")


def get_user_info_from_request(request: Request) -> Optional[UserInfo]:
    """
    从请求中获取用户信息。
    
    参数:
        request: HTTP请求
    
    返回:
        Optional[UserInfo]: 用户信息，不存在时返回None
    """
    return getattr(request.state, "user_info", None)
