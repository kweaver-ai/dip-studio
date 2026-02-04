"""
项目词典领域模型

定义项目词典相关的领域模型和实体。
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DictionaryEntry:
    """
    项目词典条目领域模型。

    用于定义项目中的术语。
    
    属性:
        id: 条目主键 ID
        project_id: 所属项目 ID
        term: 术语名称
        definition: 术语定义
        creator_id: 创建者用户 ID（UUID 字符串）
        creator_name: 创建者用户显示名
        created_at: 创建时间
        editor_id: 最近编辑者用户 ID（UUID 字符串）
        editor_name: 最近编辑者用户显示名
        edited_at: 最近编辑时间
    """
    id: int
    project_id: int
    term: str
    definition: str
    creator_id: Optional[str] = None
    creator_name: Optional[str] = None
    created_at: Optional[datetime] = None
    editor_id: Optional[str] = None
    editor_name: Optional[str] = None
    edited_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化后处理。"""
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.edited_at is None:
            self.edited_at = self.created_at
        # 如果未显式传入编辑者信息，则默认与创建者相同
        if self.editor_id is None:
            self.editor_id = self.creator_id
        if self.editor_name is None:
            self.editor_name = self.creator_name

    def validate(self) -> None:
        """
        验证词典条目数据。

        异常:
            ValueError: 当数据验证失败时抛出
        """
        if not self.term or len(self.term) > 255:
            raise ValueError("术语名称不能为空且不能超过255字符")
        if not self.definition:
            raise ValueError("术语定义不能为空")
        if not self.project_id:
            raise ValueError("项目 ID 不能为空")

    def update(
        self,
        term: Optional[str] = None,
        definition: Optional[str] = None,
        editor_id: Optional[str] = None,
        editor_name: Optional[str] = None,
    ) -> "DictionaryEntry":
        """
        更新词典条目。

        参数:
            term: 新的术语名称
            definition: 新的术语定义
            editor_id: 编辑者用户 ID（UUID 字符串）
            editor_name: 编辑者用户显示名

        返回:
            DictionaryEntry: 更新后的词典条目实例
        """
        if term is not None:
            self.term = term
        if definition is not None:
            self.definition = definition
        if editor_id is not None:
            self.editor_id = editor_id
        if editor_name is not None:
            self.editor_name = editor_name
        # 每次更新都刷新编辑时间
        self.edited_at = datetime.now()
        return self

    def to_dict(self) -> dict:
        """
        转换为字典。

        返回:
            dict: 词典条目字典
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "term": self.term,
            "definition": self.definition,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "editor_id": self.editor_id,
            "editor_name": self.editor_name,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
        }
