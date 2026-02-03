"""
领域模型模块

定义项目管理相关的领域模型和实体。
"""
from src.domains.project import Project
from src.domains.node import ProjectNode, NodeType
from src.domains.dictionary import DictionaryEntry
from src.domains.document import FunctionDocument, DocumentBlock, BlockType

__all__ = [
    "Project",
    "ProjectNode",
    "NodeType",
    "DictionaryEntry",
    "FunctionDocument",
    "DocumentBlock",
    "BlockType",
]
