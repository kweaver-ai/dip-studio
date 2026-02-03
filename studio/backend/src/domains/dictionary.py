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
        created_at: 创建时间
    """
    id: int
    project_id: int
    term: str
    definition: str
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化后处理。"""
        if self.created_at is None:
            self.created_at = datetime.now()

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
    ) -> "DictionaryEntry":
        """
        更新词典条目。

        参数:
            term: 新的术语名称
            definition: 新的术语定义

        返回:
            DictionaryEntry: 更新后的词典条目实例
        """
        if term is not None:
            self.term = term
        if definition is not None:
            self.definition = definition
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
