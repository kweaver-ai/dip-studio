"""
功能设计文档端口接口

定义功能设计文档操作的抽象接口（端口）。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.domains.document import FunctionDocument, DocumentBlock


class DocumentContentPort(ABC):
    """
    文档内容端口接口（单 JSON 对象存储，当前实现为 MariaDB）。

    文档内容存储为一个 JSON 对象 {}（含任意 kv），
    与文档初始化入参、GET 返回、增量 PATCH 目标一致。
    """

    @abstractmethod
    async def get_content(self, document_id: int) -> dict:
        """
        获取文档内容（单 JSON 对象）。

        参数:
            document_id: 文档 ID

        返回:
            dict: 文档内容，未初始化时返回 {}
        """
        pass

    @abstractmethod
    async def set_content(self, document_id: int, content: dict) -> None:
        """
        设置文档内容（文档初始化）。

        参数:
            document_id: 文档 ID
            content: 初始内容对象（含 kv）
        """
        pass

    @abstractmethod
    async def patch_content(
        self,
        document_id: int,
        patch_operations: List[dict],
    ) -> dict:
        """
        对文档内容应用 JSON Patch，并持久化。

        参数:
            document_id: 文档 ID
            patch_operations: RFC 6902 JSON Patch 操作数组

        返回:
            dict: 应用后的新内容

        异常:
            ValueError: Patch 应用失败时抛出
        """
        pass

    @abstractmethod
    async def delete_content(self, document_id: int) -> None:
        """
        删除文档内容（删除功能节点时调用）。

        参数:
            document_id: 文档 ID
        """
        pass


class DocumentPort(ABC):
    """
    功能设计文档端口接口（MariaDB）。

    这是一个输出端口，定义了与文档元信息存储的交互方式。
    """

    @abstractmethod
    async def get_document_by_id(self, document_id: int) -> FunctionDocument:
        """
        根据文档 ID 获取文档。

        参数:
            document_id: 文档 ID

        返回:
            FunctionDocument: 文档实体

        异常:
            ValueError: 当文档不存在时抛出
        """
        pass

    @abstractmethod
    async def get_document_by_id_optional(self, document_id: int) -> Optional[FunctionDocument]:
        """
        根据文档 ID 获取文档（可选）。

        参数:
            document_id: 文档 ID

        返回:
            Optional[FunctionDocument]: 文档实体，不存在时返回 None
        """
        pass

    @abstractmethod
    async def get_document_by_node_id(self, function_node_id: int) -> Optional[FunctionDocument]:
        """
        根据功能节点 ID 获取文档。

        参数:
            function_node_id: 功能节点 ID

        返回:
            Optional[FunctionDocument]: 文档实体，不存在时返回 None
        """
        pass

    @abstractmethod
    async def create_document(self, document: FunctionDocument) -> FunctionDocument:
        """
        创建新文档。

        参数:
            document: 文档实体

        返回:
            FunctionDocument: 创建后的文档实体（包含生成的 ID）
        """
        pass

    @abstractmethod
    async def update_document(self, document: FunctionDocument) -> FunctionDocument:
        """
        更新文档信息。

        参数:
            document: 文档实体

        返回:
            FunctionDocument: 更新后的文档实体

        异常:
            ValueError: 当文档不存在时抛出
        """
        pass

    @abstractmethod
    async def delete_document(self, document_id: int) -> bool:
        """
        删除文档。

        参数:
            document_id: 文档 ID

        返回:
            bool: 是否删除成功

        异常:
            ValueError: 当文档不存在时抛出
        """
        pass

    @abstractmethod
    async def delete_document_by_node_id(self, function_node_id: int) -> bool:
        """
        根据功能节点 ID 删除文档。

        参数:
            function_node_id: 功能节点 ID

        返回:
            bool: 是否删除成功
        """
        pass


class DocumentBlockPort(ABC):
    """
    文档块端口接口（当前实现为 MariaDB）。

    这是一个输出端口，定义了与文档内容块存储的交互方式。
    """

    @abstractmethod
    async def get_blocks_by_document_id(self, document_id: int) -> List[DocumentBlock]:
        """
        获取文档的所有块。

        参数:
            document_id: 文档 ID

        返回:
            List[DocumentBlock]: 文档块列表，按 order 排序
        """
        pass

    @abstractmethod
    async def get_block_by_id(self, block_id: str) -> Optional[DocumentBlock]:
        """
        根据块 ID 获取文档块。

        参数:
            block_id: 块 ID

        返回:
            Optional[DocumentBlock]: 文档块，不存在时返回 None
        """
        pass

    @abstractmethod
    async def insert_block(self, block: DocumentBlock) -> DocumentBlock:
        """
        插入新的文档块。

        参数:
            block: 文档块

        返回:
            DocumentBlock: 插入后的文档块（包含生成的 ID）
        """
        pass

    @abstractmethod
    async def update_block(self, block: DocumentBlock) -> DocumentBlock:
        """
        更新文档块。

        参数:
            block: 文档块

        返回:
            DocumentBlock: 更新后的文档块

        异常:
            ValueError: 当块不存在时抛出
        """
        pass

    @abstractmethod
    async def delete_block(self, block_id: str) -> bool:
        """
        删除文档块。

        参数:
            block_id: 块 ID

        返回:
            bool: 是否删除成功
        """
        pass

    @abstractmethod
    async def delete_blocks_by_document_id(self, document_id: int) -> int:
        """
        删除文档的所有块。

        参数:
            document_id: 文档 ID

        返回:
            int: 删除的块数量
        """
        pass

    @abstractmethod
    async def get_max_order(self, document_id: int) -> int:
        """
        获取文档中块的最大排序值。

        参数:
            document_id: 文档 ID

        返回:
            int: 最大排序值
        """
        pass

    @abstractmethod
    async def replace_blocks(
        self,
        document_id: int,
        blocks: List[DocumentBlock],
    ) -> List[DocumentBlock]:
        """
        用新块列表替换文档的全部块（用于 JSON Patch 应用后的持久化）。

        参数:
            document_id: 文档 ID
            blocks: 新的块列表（顺序即 order）

        返回:
            List[DocumentBlock]: 持久化后的块列表
        """
        pass
