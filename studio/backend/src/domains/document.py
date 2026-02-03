"""
功能设计文档领域模型

定义功能设计文档相关的领域模型和实体。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any


class BlockType(str, Enum):
    """
    文档块类型枚举。
    
    - TEXT: 文本块
    - LIST: 列表块
    - TABLE: 表格块
    - PLUGIN: 插件块（指标/ChatKit/业务知识网络）
    """
    TEXT = "text"
    LIST = "list"
    TABLE = "table"
    PLUGIN = "plugin"


@dataclass
class DocumentBlock:
    """
    文档块领域模型。

    存储在 MariaDB 中的文档内容块。

    属性:
        id: 块唯一 ID（MariaDB BIGINT，API 以字符串返回）
        document_id: 关联的文档 ID（MariaDB function_document.id）
        type: 块类型
        content: 块内容（JSON 对象）
        order: 排序顺序
        updated_at: 更新时间
    """
    id: str
    document_id: int
    type: BlockType
    content: Any
    order: int = 0
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化后处理。"""
        if self.updated_at is None:
            self.updated_at = datetime.now()
        # 确保 type 是 BlockType 枚举
        if isinstance(self.type, str):
            self.type = BlockType(self.type)

    def validate(self) -> None:
        """
        验证文档块数据。

        异常:
            ValueError: 当数据验证失败时抛出
        """
        if not self.document_id:
            raise ValueError("文档 ID 不能为空")
        if self.content is None:
            raise ValueError("块内容不能为空")

    def update_content(self, content: Any) -> "DocumentBlock":
        """
        更新块内容。

        参数:
            content: 新的块内容

        返回:
            DocumentBlock: 更新后的文档块实例
        """
        self.content = content
        self.updated_at = datetime.now()
        return self

    def to_dict(self) -> dict:
        """
        转换为字典（用于存储）。

        返回:
            dict: 文档块字典
        """
        return {
            "_id": self.id,
            "document_id": self.document_id,
            "type": self.type.value,
            "content": self.content,
            "order": self.order,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentBlock":
        """
        从字典创建文档块实例。

        参数:
            data: 文档数据字典

        返回:
            DocumentBlock: 文档块实例
        """
        return cls(
            id=str(data.get("_id", "")),
            document_id=data.get("document_id", 0),
            type=BlockType(data.get("type", "text")),
            content=data.get("content"),
            order=data.get("order", 0),
            updated_at=data.get("updated_at"),
        )


@dataclass
class FunctionDocument:
    """
    功能设计文档领域模型。

    存储在 MariaDB 中的文档元信息。

    属性:
        id: 文档主键 ID
        function_node_id: 关联的功能节点 ID
        creator: 创建者用户 ID
        created_at: 创建时间
        editor: 最近编辑者用户 ID
        edited_at: 最近编辑时间
        blocks: 文档块列表（查询时填充）
    """
    id: int
    function_node_id: int
    creator: int = 0
    created_at: Optional[datetime] = None
    editor: int = 0
    edited_at: Optional[datetime] = None
    blocks: List[DocumentBlock] = field(default_factory=list)

    def __post_init__(self):
        """初始化后处理。"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.edited_at is None:
            self.edited_at = self.created_at
        if self.editor == 0:
            self.editor = self.creator

    def validate(self) -> None:
        """
        验证文档数据。

        异常:
            ValueError: 当数据验证失败时抛出
        """
        if not self.function_node_id:
            raise ValueError("功能节点 ID 不能为空")

    def update_editor(self, editor: int) -> "FunctionDocument":
        """
        更新编辑者信息。

        参数:
            editor: 编辑者用户 ID

        返回:
            FunctionDocument: 更新后的文档实例
        """
        self.editor = editor
        self.edited_at = datetime.now()
        return self

    def add_block(self, block: DocumentBlock) -> None:
        """
        添加文档块。

        参数:
            block: 文档块
        """
        self.blocks.append(block)

    def to_dict(self) -> dict:
        """
        转换为字典。

        返回:
            dict: 文档字典
        """
        return {
            "id": self.id,
            "function_node_id": self.function_node_id,
            "creator": self.creator,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "editor": self.editor,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "blocks": [block.to_dict() for block in self.blocks],
        }
