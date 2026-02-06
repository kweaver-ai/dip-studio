"""
功能设计文档 API Schema

定义功能设计文档相关的 API 请求和响应模型。
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============ 请求模型 ============
# 文档初始化已合并到创建功能节点时自动执行（空 {}），无单独初始化接口

# RFC 6902 JSON Patch 单条操作（用于 OpenAPI 文档）
class JsonPatchOperation(BaseModel):
    """RFC 6902 JSON Patch 单条操作。Patch 应用目标为 {\"blocks\": [块数组]}。"""
    op: str = Field(..., description="操作类型: add/remove/replace/move/copy/test")
    path: str = Field(..., description="JSON Pointer 路径，如 /blocks/0、/blocks/0/content、/blocks/-")
    value: Optional[Any] = Field(None, description="值（add/replace 等需要）")
    from_: Optional[str] = Field(None, alias="from", description="源路径（move/copy 需要）")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


# ============ 响应模型 ============

class DocumentBlockResponse(BaseModel):
    """文档块响应。"""
    id: str = Field(..., description="块 ID")
    document_id: int = Field(..., description="文档 ID")
    type: str = Field(..., description="块类型：text/list/table/plugin")
    content: Any = Field(..., description="块内容")
    order: int = Field(..., description="排序顺序")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class DocumentContentResponse(BaseModel):
    """文档内容响应（与 PATCH 操作目标一致的整体 JSON）。"""
    blocks: List[DocumentBlockResponse] = Field(..., description="文档块数组")

    model_config = ConfigDict(from_attributes=True)


class PatchDocumentResponse(BaseModel):
    """文档增量更新响应：仅返回是否更新成功。"""
    success: bool = Field(..., description="是否更新成功")

    model_config = ConfigDict(from_attributes=True)


class FunctionDocumentResponse(BaseModel):
    """功能设计文档响应（含元信息，内部使用）。"""
    id: int = Field(..., description="文档 ID")
    function_node_id: str = Field(..., description="功能节点 ID (UUID)")
    creator_id: str = Field("", description="创建者用户 ID（UUID）")
    creator_name: str = Field("", description="创建者用户显示名")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    editor_id: str = Field("", description="最近编辑者用户 ID（UUID）")
    editor_name: str = Field("", description="最近编辑者用户显示名")
    edited_at: Optional[datetime] = Field(None, description="最近编辑时间")
    blocks: List[DocumentBlockResponse] = Field(default_factory=list, description="文档块列表")

    model_config = ConfigDict(from_attributes=True)
