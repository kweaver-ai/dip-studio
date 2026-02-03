"""
功能设计文档服务

应用层服务，负责编排功能设计文档管理操作。
"""
import copy
import logging
from typing import Any, List, Optional

import jsonpatch

from src.domains.document import FunctionDocument, DocumentBlock, BlockType
from src.ports.document_port import DocumentPort, DocumentBlockPort, DocumentContentPort
from src.ports.node_port import NodePort

logger = logging.getLogger(__name__)


def _block_to_patch_doc(block: DocumentBlock) -> dict:
    """将文档块转为可被 JSON Patch 操作的 JSON 结构。"""
    return {
        "id": block.id,
        "document_id": block.document_id,
        "type": block.type.value,
        "content": copy.deepcopy(block.content) if block.content is not None else {},
        "order": block.order,
        "updated_at": block.updated_at.isoformat() if block.updated_at else None,
    }


def _patch_doc_to_block(item: dict, document_id: int) -> DocumentBlock:
    """将 JSON Patch 应用后的块字典转为 DocumentBlock。"""
    return DocumentBlock(
        id=str(item.get("id") or ""),
        document_id=document_id,
        type=BlockType(item.get("type", "text")),
        content=item.get("content"),
        order=int(item.get("order", 0)),
        updated_at=None,
    )


class DocumentService:
    """
    功能设计文档服务。

    该服务属于应用层，通过端口编排文档管理的业务逻辑。
    """

    def __init__(
        self,
        document_port: DocumentPort,
        document_block_port: DocumentBlockPort,
        document_content_port: DocumentContentPort,
        node_port: Optional[NodePort] = None,
    ):
        """
        初始化文档服务。

        参数:
            document_port: 文档端口实现（MariaDB）
            document_block_port: 文档块端口实现（MariaDB）
            document_content_port: 文档内容端口实现（MariaDB，单 JSON 对象）
            node_port: 节点端口实现（用于验证节点状态）
        """
        self._document_port = document_port
        self._document_block_port = document_block_port
        self._document_content_port = document_content_port
        self._node_port = node_port

    async def get_document_by_node_id(
        self,
        function_node_id: int,
        include_blocks: bool = True,
    ) -> Optional[FunctionDocument]:
        """
        根据功能节点 ID 获取文档。

        参数:
            function_node_id: 功能节点 ID
            include_blocks: 是否包含文档块

        返回:
            Optional[FunctionDocument]: 文档实体，不存在时返回 None
        """
        document = await self._document_port.get_document_by_node_id(function_node_id)
        if document is None:
            return None
        
        if include_blocks:
            blocks = await self._document_block_port.get_blocks_by_document_id(document.id)
            document.blocks = blocks
        
        return document

    async def get_document_by_id(
        self,
        document_id: int,
        include_blocks: bool = True,
    ) -> FunctionDocument:
        """
        根据文档 ID 获取文档。

        参数:
            document_id: 文档 ID
            include_blocks: 是否包含文档块

        返回:
            FunctionDocument: 文档实体

        异常:
            ValueError: 当文档不存在时抛出
        """
        document = await self._document_port.get_document_by_id(document_id)
        
        if include_blocks:
            blocks = await self._document_block_port.get_blocks_by_document_id(document.id)
            document.blocks = blocks
        
        return document

    async def patch_document_blocks(
        self,
        document_id: int,
        patch_operations: List[dict],
        editor: int = 0,
    ) -> FunctionDocument:
        """
        使用 JSON Patch (RFC 6902) 更新文档块。

        Patch 应用目标为 {"blocks": [块数组]}，path 示例：/blocks/0/content、/blocks/- 等。

        参数:
            document_id: 文档 ID
            patch_operations: RFC 6902 的 patch 操作列表，如 [{"op": "replace", "path": "/blocks/0/content", "value": {...}}]
            editor: 编辑者用户 ID

        返回:
            FunctionDocument: 更新后的文档（包含所有块）

        异常:
            ValueError: 当文档不存在或 patch 无效时抛出
        """
        document = await self._document_port.get_document_by_id(document_id)
        blocks = await self._document_block_port.get_blocks_by_document_id(document_id)
        doc = {"blocks": [_block_to_patch_doc(b) for b in blocks]}
        try:
            patched = jsonpatch.apply_patch(doc, patch_operations)
        except jsonpatch.JsonPatchException as e:
            raise ValueError(f"JSON Patch 应用失败: {e}") from e

        blocks_list = patched.get("blocks")
        if not isinstance(blocks_list, list):
            raise ValueError("patch 结果中 blocks 必须为数组")

        new_blocks = [
            _patch_doc_to_block(item, document_id)
            for item in blocks_list
        ]
        saved = await self._document_block_port.replace_blocks(document_id, new_blocks)
        document.update_editor(editor)
        await self._document_port.update_document(document)
        document.blocks = saved
        return document

    async def get_blocks_by_document_id(self, document_id: int) -> List[DocumentBlock]:
        """
        获取文档的所有块。

        参数:
            document_id: 文档 ID

        返回:
            List[DocumentBlock]: 文档块列表
        """
        return await self._document_block_port.get_blocks_by_document_id(document_id)

    async def init_document(
        self,
        function_node_id: int,
        creator: int = 0,
    ) -> tuple[int, FunctionDocument]:
        """
        初始化文档（适配 TipTap + fast-json-patch 前端方案）。
        若该功能节点已有文档则返回该文档；否则创建新文档并回写 document_id 到节点。

        参数:
            function_node_id: 功能节点 ID
            creator: 创建者用户 ID

        返回:
            tuple[int, FunctionDocument]: (document_id, 文档实体，含 blocks)

        异常:
            ValueError: 当节点不存在或非功能节点时抛出
        """
        document = await self._document_port.get_document_by_node_id(function_node_id)
        if document is not None:
            blocks = await self._document_block_port.get_blocks_by_document_id(document.id)
            document.blocks = blocks
            return document.id, document

        if not self._node_port:
            raise ValueError("无法创建文档：未配置节点端口")
        node = await self._node_port.get_node_by_id_optional(function_node_id)
        if node is None:
            raise ValueError(f"功能节点不存在: {function_node_id}")
        from src.domains.node import NodeType
        if node.node_type != NodeType.FUNCTION:
            raise ValueError("仅功能节点可初始化文档")

        doc = FunctionDocument(
            id=0,
            function_node_id=function_node_id,
            creator=creator,
        )
        doc = await self._document_port.create_document(doc)
        await self._node_port.update_node_document_id(function_node_id, doc.id)
        doc.blocks = []
        logger.info(f"初始化文档: function_node_id={function_node_id}, document_id={doc.id}")
        return doc.id, doc

    # ---------- 文档内容（单 JSON 对象 {}，适配 TipTap + fast-json-patch） ----------

    async def get_document_content(self, document_id: int) -> dict:
        """
        获取文档内容（单 JSON 对象）。
        创建功能节点时已生成 document_id 并初始化为空 {}。

        参数:
            document_id: 文档 ID

        返回:
            dict: 文档内容对象
        """
        # 校验文档是否存在（不存在时 get_document_by_id 会抛 ValueError）
        await self._document_port.get_document_by_id(document_id)
        return await self._document_content_port.get_content(document_id)

    async def patch_document_content(
        self,
        document_id: int,
        patch_operations: List[dict],
    ) -> dict:
        """
        对文档内容 {} 进行增量更新（JSON Patch），返回更新后的内容。

        参数:
            document_id: 文档 ID
            patch_operations: RFC 6902 JSON Patch 操作数组

        返回:
            dict: 更新后的文档内容

        异常:
            ValueError: 文档不存在或 Patch 失败时抛出
        """
        await self._document_port.get_document_by_id(document_id)
        return await self._document_content_port.patch_content(document_id, patch_operations)
