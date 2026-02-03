"""
异常处理模块

定义业务异常和错误响应格式。
"""
from typing import Optional, Any
from fastapi import status
from fastapi.responses import JSONResponse


class BusinessException(Exception):
    """
    业务异常基类。
    
    所有业务异常都应该继承此类。
    """
    
    def __init__(
        self,
        status_code: int,
        code: str,
        description: str,
        solution: Optional[str] = None,
        detail: Optional[Any] = None,
    ):
        """
        初始化业务异常。
        
        参数:
            status_code: HTTP 状态码
            code: 业务错误码
            description: 错误描述
            solution: 解决方案建议
            detail: 详细信息
        """
        super().__init__(description)
        self.status_code = status_code
        self.code = code
        self.description = description
        self.solution = solution
        self.detail = detail
    
    def to_response(self) -> JSONResponse:
        """
        转换为 JSON 响应。
        
        返回:
            JSONResponse: JSON 响应
        """
        content = {
            "code": self.code,
            "description": self.description,
        }
        if self.solution:
            content["solution"] = self.solution
        if self.detail:
            content["detail"] = self.detail
        
        return JSONResponse(
            status_code=self.status_code,
            content=content,
        )


class ValidationError(BusinessException):
    """请求参数验证错误。"""
    
    def __init__(
        self,
        code: str = "VALIDATION_ERROR",
        description: str = "请求参数验证失败",
        solution: Optional[str] = "请检查请求参数格式是否正确",
        detail: Optional[Any] = None,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=code,
            description=description,
            solution=solution,
            detail=detail,
        )


class NotFoundError(BusinessException):
    """资源不存在错误。"""
    
    def __init__(
        self,
        code: str = "NOT_FOUND",
        description: str = "资源不存在",
        solution: Optional[str] = "请检查资源 ID 是否正确",
        detail: Optional[Any] = None,
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=code,
            description=description,
            solution=solution,
            detail=detail,
        )


class ConflictError(BusinessException):
    """资源冲突错误。"""
    
    def __init__(
        self,
        code: str = "CONFLICT",
        description: str = "资源冲突",
        solution: Optional[str] = None,
        detail: Optional[Any] = None,
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code=code,
            description=description,
            solution=solution,
            detail=detail,
        )


class UnauthorizedError(BusinessException):
    """未授权错误。"""
    
    def __init__(
        self,
        code: str = "UNAUTHORIZED",
        description: str = "未授权访问",
        solution: Optional[str] = "请先登录",
        detail: Optional[Any] = None,
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=code,
            description=description,
            solution=solution,
            detail=detail,
        )


class ForbiddenError(BusinessException):
    """禁止访问错误。"""
    
    def __init__(
        self,
        code: str = "FORBIDDEN",
        description: str = "禁止访问",
        solution: Optional[str] = "您没有权限执行此操作",
        detail: Optional[Any] = None,
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code=code,
            description=description,
            solution=solution,
            detail=detail,
        )


class InternalError(BusinessException):
    """内部服务器错误。"""
    
    def __init__(
        self,
        code: str = "INTERNAL_ERROR",
        description: str = "服务器内部错误",
        solution: Optional[str] = "请稍后重试或联系管理员",
        detail: Optional[Any] = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=code,
            description=description,
            solution=solution,
            detail=detail,
        )


def create_error_response(
    status_code: int,
    code: str,
    description: str,
    solution: Optional[str] = None,
    detail: Optional[Any] = None,
) -> JSONResponse:
    """
    创建错误响应。
    
    参数:
        status_code: HTTP 状态码
        code: 业务错误码
        description: 错误描述
        solution: 解决方案建议
        detail: 详细信息
    
    返回:
        JSONResponse: JSON 响应
    """
    content = {
        "code": code,
        "description": description,
    }
    if solution:
        content["solution"] = solution
    if detail:
        content["detail"] = detail
    
    return JSONResponse(
        status_code=status_code,
        content=content,
    )
