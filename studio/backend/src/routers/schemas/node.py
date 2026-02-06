"""
节点 API Schema

定义节点相关的 API 请求和响应模型。
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============ 请求模型 ============

class CreateApplicationNodeRequest(BaseModel):
    """创建应用节点请求。"""
    project_id: int = Field(..., description="项目 ID")
    name: str = Field(..., description="节点名称", max_length=255)
    description: Optional[str] = Field(None, description="节点描述")


class CreatePageNodeRequest(BaseModel):
    """创建页面节点请求。"""
    project_id: int = Field(..., description="项目 ID")
    parent_id: str = Field(..., description="父节点 ID（应用节点，UUID）")
    name: str = Field(..., description="节点名称", max_length=255)
    description: Optional[str] = Field(None, description="节点描述")


class CreateFunctionNodeRequest(BaseModel):
    """创建功能节点请求。"""
    project_id: int = Field(..., description="项目 ID")
    parent_id: str = Field(..., description="父节点 ID（页面节点，UUID）")
    name: str = Field(..., description="节点名称", max_length=255)
    description: Optional[str] = Field(None, description="节点描述")


class UpdateNodeRequest(BaseModel):
    """更新节点请求。"""
    name: Optional[str] = Field(None, description="节点名称", max_length=255)
    description: Optional[str] = Field(None, description="节点描述")


class MoveNodeRequest(BaseModel):
    """移动节点请求。"""
    node_id: str = Field(..., description="节点 ID (UUID)")
    new_parent_id: Optional[str] = Field(None, description="新父节点 ID (UUID)")
    predecessor_node_id: Optional[str] = Field(
        None,
        description="前置节点 ID（新父节点下的直接子节点，移动后位于该节点之后）；不传或 null 表示放到第一个",
    )


# ============ 响应模型 ============

class NodeResponse(BaseModel):
    """节点响应。"""
    id: str = Field(..., description="节点 ID (UUID)")
    project_id: int = Field(..., description="项目 ID")
    parent_id: Optional[str] = Field(None, description="父节点 ID (UUID)")
    node_type: str = Field(..., description="节点类型：application/page/function")
    name: str = Field(..., description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")
    path: str = Field(..., description="节点路径")
    sort: int = Field(..., description="排序值")
    status: int = Field(..., description="节点状态")
    document_id: Optional[int] = Field(None, description="功能节点关联的文档 ID")
    creator_id: str = Field("", description="创建者用户 ID（UUID）")
    creator_name: str = Field("", description="创建者用户显示名")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    editor_id: str = Field("", description="最近编辑者用户 ID（UUID）")
    editor_name: str = Field("", description="最近编辑者用户显示名")
    edited_at: Optional[datetime] = Field(None, description="最近编辑时间")

    model_config = ConfigDict(from_attributes=True)


class NodeTreeResponse(BaseModel):
    """节点树响应（children 按 sort 顺序，响应中不包含 sort）。"""
    id: str = Field(..., description="节点 ID (UUID)")
    project_id: int = Field(..., description="项目 ID")
    parent_id: Optional[str] = Field(None, description="父节点 ID (UUID)")
    node_type: str = Field(..., description="节点类型")
    name: str = Field(..., description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")
    path: str = Field(..., description="节点路径")
    status: int = Field(..., description="节点状态")
    document_id: Optional[int] = Field(None, description="功能节点关联的文档 ID")
    creator_id: str = Field("", description="创建者用户 ID（UUID）")
    creator_name: str = Field("", description="创建者用户显示名")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    editor_id: str = Field("", description="最近编辑者用户 ID（UUID）")
    editor_name: str = Field("", description="最近编辑者用户显示名")
    edited_at: Optional[datetime] = Field(None, description="最近编辑时间")
    children: List["NodeTreeResponse"] = Field(default_factory=list, description="子节点列表（按 sort 顺序）")

    model_config = ConfigDict(from_attributes=True)


# 更新前向引用
NodeTreeResponse.model_rebuild()
