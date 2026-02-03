"""
节点领域模型

定义项目节点相关的领域模型和实体。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class NodeType(str, Enum):
    """
    节点类型枚举。
    
    - APPLICATION: 应用节点，根节点，一个项目只能有一个
    - PAGE: 页面节点，只能在应用节点下创建
    - FUNCTION: 功能节点，只能在页面节点下创建
    """
    APPLICATION = "application"
    PAGE = "page"
    FUNCTION = "function"

    @classmethod
    def get_allowed_parent_types(cls, node_type: "NodeType") -> List[Optional["NodeType"]]:
        """
        获取节点类型允许的父节点类型。

        参数:
            node_type: 节点类型

        返回:
            List[Optional[NodeType]]: 允许的父节点类型列表
        """
        mapping = {
            cls.APPLICATION: [None],  # 应用节点只能作为根节点
            cls.PAGE: [cls.APPLICATION],  # 页面节点只能在应用节点下
            cls.FUNCTION: [cls.PAGE],  # 功能节点只能在页面节点下
        }
        return mapping.get(node_type, [])

    @classmethod
    def can_have_children(cls, node_type: "NodeType") -> bool:
        """
        检查节点类型是否可以有子节点。

        参数:
            node_type: 节点类型

        返回:
            bool: 是否可以有子节点
        """
        # 功能节点不能有子节点
        return node_type != cls.FUNCTION


@dataclass
class ProjectNode:
    """
    项目节点领域模型。

    统一管理 application/page/function 节点。

    属性:
        id: 节点主键 ID
        project_id: 所属项目 ID
        parent_id: 父节点 ID（根节点为 None）
        node_type: 节点类型
        name: 节点名称
        description: 节点描述
        path: 节点路径，如 /node_1/node_3/node_8
        sort: 同级排序
        status: 节点状态
        document_id: 功能节点关联的文档 ID（仅 node_type=function 时有值）
        creator: 创建者用户 ID
        created_at: 创建时间
        editor: 最近编辑者用户 ID
        edited_at: 最近编辑时间
        children: 子节点列表（用于树结构）
    """
    id: int
    project_id: int
    node_type: NodeType
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    path: str = ""
    sort: int = 0
    status: int = 1
    document_id: Optional[int] = None  # 功能节点关联的文档 ID
    creator: int = 0
    created_at: Optional[datetime] = None
    editor: int = 0
    edited_at: Optional[datetime] = None
    children: List["ProjectNode"] = field(default_factory=list)

    def __post_init__(self):
        """初始化后处理。"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.edited_at is None:
            self.edited_at = self.created_at
        if self.editor == 0:
            self.editor = self.creator
        # 确保 node_type 是 NodeType 枚举
        if isinstance(self.node_type, str):
            self.node_type = NodeType(self.node_type)

    def validate(self) -> None:
        """
        验证节点数据。

        异常:
            ValueError: 当数据验证失败时抛出
        """
        if not self.name or len(self.name) > 255:
            raise ValueError("节点名称不能为空且不能超过255字符")
        if not self.project_id:
            raise ValueError("项目 ID 不能为空")

    def validate_parent(self, parent_node: Optional["ProjectNode"]) -> None:
        """
        验证父节点是否合法。

        参数:
            parent_node: 父节点，根节点时为 None

        异常:
            ValueError: 当父节点类型不合法时抛出
        """
        allowed_parents = NodeType.get_allowed_parent_types(self.node_type)
        
        if parent_node is None:
            if None not in allowed_parents:
                raise ValueError(f"{self.node_type.value} 节点必须有父节点")
        else:
            if parent_node.node_type not in allowed_parents:
                raise ValueError(
                    f"{self.node_type.value} 节点不能在 {parent_node.node_type.value} 节点下创建"
                )

    def can_have_children(self) -> bool:
        """
        检查当前节点是否可以有子节点。

        返回:
            bool: 是否可以有子节点
        """
        return NodeType.can_have_children(self.node_type)

    def build_path(self, parent_path: str = "") -> str:
        """
        构建节点路径。

        参数:
            parent_path: 父节点路径

        返回:
            str: 完整的节点路径
        """
        if parent_path:
            self.path = f"{parent_path}/node_{self.id}"
        else:
            self.path = f"/node_{self.id}"
        return self.path

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        sort: Optional[int] = None,
        editor: Optional[int] = None,
    ) -> "ProjectNode":
        """
        更新节点信息。

        参数:
            name: 新的节点名称
            description: 新的节点描述
            sort: 新的排序值
            editor: 编辑者用户 ID

        返回:
            ProjectNode: 更新后的节点实例
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if sort is not None:
            self.sort = sort
        if editor is not None:
            self.editor = editor
        self.edited_at = datetime.now()
        return self

    def add_child(self, child: "ProjectNode") -> None:
        """
        添加子节点。

        参数:
            child: 子节点
        """
        self.children.append(child)

    def to_dict(self, include_children: bool = True) -> dict:
        """
        转换为字典。

        参数:
            include_children: 是否包含子节点

        返回:
            dict: 节点字典
        """
        result = {
            "id": self.id,
            "project_id": self.project_id,
            "parent_id": self.parent_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "sort": self.sort,
            "status": self.status,
            "document_id": self.document_id,
            "creator": self.creator,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "editor": self.editor,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
        }
        if include_children:
            result["children"] = [child.to_dict() for child in self.children]
        return result
