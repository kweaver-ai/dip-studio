"""
项目词典 API Schema

定义项目词典相关的 API 请求和响应模型。
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============ 请求模型 ============

class CreateDictionaryEntryRequest(BaseModel):
    """创建词典条目请求。"""
    project_id: int = Field(..., description="项目 ID")
    term: str = Field(..., description="术语名称", max_length=255)
    definition: str = Field(..., description="术语定义")


class UpdateDictionaryEntryRequest(BaseModel):
    """更新词典条目请求。"""
    term: Optional[str] = Field(None, description="术语名称", max_length=255)
    definition: Optional[str] = Field(None, description="术语定义")


# ============ 响应模型 ============

class DictionaryEntryResponse(BaseModel):
    """词典条目响应。"""
    id: int = Field(..., description="条目 ID")
    project_id: int = Field(..., description="项目 ID")
    term: str = Field(..., description="术语名称")
    definition: str = Field(..., description="术语定义")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    model_config = ConfigDict(from_attributes=True)
