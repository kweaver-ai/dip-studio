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
        creator: 创建者用户 ID
        created_at: 创建时间
        editor: 最近编辑者用户 ID
        edited_at: 最近编辑时间
    """
    id: int
    name: str
    description: Optional[str] = None
    creator: int = 0
    created_at: Optional[datetime] = None
    editor: int = 0
    edited_at: Optional[datetime] = None

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
        editor: Optional[int] = None,
    ) -> "Project":
        """
        更新项目信息。

        参数:
            name: 新的项目名称
            description: 新的项目描述
            editor: 编辑者用户 ID

        返回:
            Project: 更新后的项目实例
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if editor is not None:
            self.editor = editor
        self.edited_at = datetime.now()
        return self
