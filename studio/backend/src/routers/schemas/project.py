"""
项目 API Schema

定义项目相关的 API 请求和响应模型。
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============ 请求模型 ============

class CreateProjectRequest(BaseModel):
    """创建项目请求。"""
    name: str = Field(..., description="项目名称", max_length=128)
    description: Optional[str] = Field(None, description="项目描述", max_length=400)


class UpdateProjectRequest(BaseModel):
    """更新项目请求。"""
    name: Optional[str] = Field(None, description="项目名称", max_length=128)
    description: Optional[str] = Field(None, description="项目描述", max_length=400)


# ============ 响应模型 ============

class ProjectResponse(BaseModel):
    """项目响应。"""
    id: int = Field(..., description="项目 ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    creator: int = Field(..., description="创建者用户 ID")
    created_at: datetime = Field(..., description="创建时间")
    editor: int = Field(..., description="最近编辑者用户 ID")
    edited_at: datetime = Field(..., description="最近编辑时间")

    model_config = ConfigDict(from_attributes=True)


# ============ 错误响应 ============

class ErrorResponse(BaseModel):
    """错误响应。"""
    code: str = Field(..., description="错误码")
    description: str = Field(..., description="错误描述")
    solution: Optional[str] = Field(None, description="解决方案")
    detail: Optional[dict] = Field(None, description="详细信息")
