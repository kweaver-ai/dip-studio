"""
项目领域模型

定义项目相关的领域模型和实体。
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    """
    项目领域模型。

    属性:
        id: 项目主键 ID
        name: 项目名称（最多128字符）
        description: 项目描述（最多400字符）
        creator_id: 创建者用户 ID（UUID 字符串）
        creator_name: 创建者用户显示名
        created_at: 创建时间
        editor_id: 最近编辑者用户 ID（UUID 字符串）
        editor_name: 最近编辑者用户显示名
        edited_at: 最近编辑时间
    """
    id: int
    name: str
    description: Optional[str] = None
    creator_id: str = ""
    creator_name: str = ""
    created_at: Optional[datetime] = None
    editor_id: str = ""
    editor_name: str = ""
    edited_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化后处理。"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.edited_at is None:
            self.edited_at = self.created_at
        # 如果未显式传入编辑者信息，则默认与创建者相同
        if not self.editor_id:
            self.editor_id = self.creator_id
        if not self.editor_name:
            self.editor_name = self.creator_name

    def validate(self) -> None:
        """
        验证项目数据。

        异常:
            ValueError: 当数据验证失败时抛出
        """
        if not self.name or len(self.name) > 128:
            raise ValueError("项目名称不能为空且不能超过128字符")
        if self.description and len(self.description) > 400:
            raise ValueError("项目描述不能超过400字符")

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        editor_id: Optional[str] = None,
        editor_name: Optional[str] = None,
    ) -> "Project":
        """
        更新项目信息。

        参数:
            name: 新的项目名称
            description: 新的项目描述
            editor_id: 编辑者用户 ID（UUID 字符串）
            editor_name: 编辑者用户显示名

        返回:
            Project: 更新后的项目实例
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if editor_id is not None:
            self.editor_id = editor_id
        if editor_name is not None:
            self.editor_name = editor_name
        self.edited_at = datetime.now()
        return self
