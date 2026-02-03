"""
认证中间件

统一从请求头提取认证token并存储到request.state和TokenContext中，供后续处理使用。
同时进行token解析，获取用户信息并存储到上下文中。
对于需要认证的路径，如果没有token则拒绝访问。
"""
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.infrastructure.context.token_context import TokenContext, UserContext, UserInfo
from src.infrastructure.exceptions import UnauthorizedError

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
    
    从请求头中提取Authorization token，并存储到：
    1. request.state.auth_token - 供路由层使用
    2. TokenContext - 供适配器层统一获取
    3. UserContext - 供应用层统一获取用户信息
    
    对于需要认证的路径，如果没有token则拒绝访问。
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
        # 支持两种情况：
        # 1. 直接路径：/health, /docs 等
        # 2. 带API前缀的路径：/api/dip-studio/v1/health 等
        for public_path in PUBLIC_PATHS:
            # 直接匹配（如 /health）
            if path == public_path:
                return True
            # 匹配以公开路径结尾的路径（如 /api/dip-studio/v1/health）
            if path.endswith(public_path) or path.endswith(public_path + "/"):
                return True
            # 匹配以公开路径开头的路径（如 /docs, /redoc）
            if path.startswith(public_path + "/") or path.startswith(public_path + "?"):
                return True
        return False
    
    def _parse_user_from_token(self, token: str) -> Optional[UserInfo]:
        """
        从token中解析用户信息。
        
        注意：这是一个简化实现。在实际生产环境中，
        应该调用外部认证服务（如Hydra）进行token内省。
        
        参数:
            token: 认证token
        
        返回:
            Optional[UserInfo]: 用户信息，解析失败返回None
        """
        # TODO: 实现实际的token解析逻辑
        # 这里返回一个默认用户，实际应该：
        # 1. 调用认证服务进行token内省
        # 2. 获取用户ID
        # 3. 查询用户详细信息
        
        # 临时实现：返回一个默认用户
        # 当接入真实认证服务时，需要替换此逻辑
        if token:
            return UserInfo(
                id=0,  # 默认用户ID
                account="anonymous",
                vision_name="匿名用户",
            )
        return None
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        处理请求，提取认证token并获取用户信息。
        
        参数:
            request: 请求对象
            call_next: 下一个中间件或路由处理函数
        
        返回:
            Response: HTTP响应
        """
        # 获取请求路径
        path = request.url.path
        
        # 如果是公开路径，直接放行
        if self._is_public_path(path):
            try:
                response = await call_next(request)
                return response
            finally:
                # 清除上下文
                TokenContext.clear_token()
                UserContext.clear_user_info()
        
        # 从请求头提取Authorization token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(f"请求路径 {path} 需要认证，但未提供token")
            error = UnauthorizedError(
                description="访问此资源需要认证",
                solution="请在请求头中提供有效的Authorization token",
            )
            return error.to_response()
        
        # 提取纯token（去除 "Bearer " 前缀）
        if auth_header.startswith("Bearer "):
            auth_token = auth_header[7:]  # 去除 "Bearer " 前缀
        else:
            # 兼容直接传递token的情况
            auth_token = auth_header
        
        if not auth_token:
            logger.warning(f"请求路径 {path} 需要认证，但token为空")
            error = UnauthorizedError(
                description="访问此资源需要认证",
                solution="请在请求头中提供有效的Authorization token",
            )
            return error.to_response()
        
        # 存储完整的Authorization header到request.state中，供路由层使用
        request.state.auth_token = auth_header
        
        # 存储纯token到TokenContext中，供适配器层统一获取
        TokenContext.set_token(auth_token)
        
        # 解析用户信息
        user_info = self._parse_user_from_token(auth_token)
        if user_info is None:
            logger.warning(f"无法从token解析用户信息: {path}")
            error = UnauthorizedError(
                description="Token无效或已过期",
                solution="请使用有效的token重新登录",
            )
            return error.to_response()
        
        # 存储用户信息到UserContext中，供应用层统一获取
        UserContext.set_user_info(user_info)
        
        # 同时存储到request.state中
        request.state.user_id = user_info.id
        request.state.user_info = user_info
        
        try:
            # 继续处理请求
            response = await call_next(request)
            return response
        finally:
            # 请求处理完成后清除上下文，避免上下文污染
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


def get_user_id_from_request(request: Request) -> int:
    """
    从请求中获取用户ID。
    
    参数:
        request: HTTP请求
    
    返回:
        int: 用户ID，不存在时返回0
    """
    return getattr(request.state, "user_id", 0)


def get_user_info_from_request(request: Request) -> Optional[UserInfo]:
    """
    从请求中获取用户信息。
    
    参数:
        request: HTTP请求
    
    返回:
        Optional[UserInfo]: 用户信息，不存在时返回None
    """
    return getattr(request.state, "user_info", None)
