"""
端口接口模块

定义领域层与基础设施层之间的契约。
"""
from src.ports.project_port import ProjectPort
from src.ports.node_port import NodePort
from src.ports.dictionary_port import DictionaryPort
from src.ports.document_port import DocumentPort, DocumentBlockPort, DocumentContentPort

__all__ = [
    "ProjectPort",
    "NodePort",
    "DictionaryPort",
    "DocumentPort",
    "DocumentBlockPort",
    "DocumentContentPort",
]
