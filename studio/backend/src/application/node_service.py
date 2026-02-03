"""
节点服务

应用层服务，负责编排节点管理操作。
"""
import logging
from typing import List, Optional, Dict

from src.domains.node import ProjectNode, NodeType
from src.utils.tiptap import tiptap_json_to_readable_text
from src.domains.document import FunctionDocument
from src.ports.node_port import NodePort
from src.ports.project_port import ProjectPort
from src.ports.document_port import DocumentPort, DocumentBlockPort, DocumentContentPort

logger = logging.getLogger(__name__)


class NodeService:
    """
    节点服务。

    该服务属于应用层，通过端口编排节点管理的业务逻辑。
    """

    def __init__(
        self,
        node_port: NodePort,
        project_port: Optional[ProjectPort] = None,
        document_port: Optional[DocumentPort] = None,
        document_block_port: Optional[DocumentBlockPort] = None,
        document_content_port: Optional[DocumentContentPort] = None,
    ):
        """
        初始化节点服务。

        参数:
            node_port: 节点端口实现
            project_port: 项目端口实现（用于验证项目存在）
            document_port: 文档端口实现（用于创建/删除功能文档）
            document_block_port: 文档块端口实现（用于删除文档块）
            document_content_port: 文档内容端口实现（创建时初始化为 {}，删除时删除内容）
        """
        self._node_port = node_port
        self._project_port = project_port
        self._document_port = document_port
        self._document_block_port = document_block_port
        self._document_content_port = document_content_port

    async def get_node_tree(self, project_id: int) -> Optional[ProjectNode]:
        """
        获取项目的节点树。

        参数:
            project_id: 项目 ID

        返回:
            Optional[ProjectNode]: 根节点（包含子节点树），不存在时返回 None
        """
        # 获取所有节点
        nodes = await self._node_port.get_nodes_by_project_id(project_id)
        if not nodes:
            return None
        
        # 构建节点映射
        node_map: Dict[int, ProjectNode] = {node.id: node for node in nodes}
        
        # 清空子节点列表（避免重复）
        for node in nodes:
            node.children = []
        
        # 构建树结构
        root = None
        for node in nodes:
            if node.parent_id is None:
                root = node
            elif node.parent_id in node_map:
                node_map[node.parent_id].add_child(node)

        # children 按 sort 顺序
        for n in node_map.values():
            n.children.sort(key=lambda c: c.sort)

        return root

    async def create_application_node(
        self,
        project_id: int,
        name: str,
        description: Optional[str] = None,
        creator: int = 0,
    ) -> ProjectNode:
        """
        创建应用节点（根节点）。

        一个项目只能有一个应用节点。

        参数:
            project_id: 项目 ID
            name: 节点名称
            description: 节点描述
            creator: 创建者用户 ID

        返回:
            ProjectNode: 创建后的节点

        异常:
            ValueError: 当项目已有应用节点时抛出
        """
        # 验证项目存在
        if self._project_port:
            await self._project_port.get_project_by_id(project_id)
        
        # 检查是否已有应用节点
        existing = await self._node_port.get_root_node(project_id)
        if existing:
            raise ValueError("项目已存在应用节点，一个项目只能有一个应用节点")
        
        node = ProjectNode(
            id=0,
            project_id=project_id,
            node_type=NodeType.APPLICATION,
            name=name,
            parent_id=None,
            description=description,
            sort=0,
            creator=creator,
        )
        node.validate()
        
        return await self._node_port.create_node(node)

    async def create_page_node(
        self,
        project_id: int,
        parent_id: int,
        name: str,
        description: Optional[str] = None,
        creator: int = 0,
    ) -> ProjectNode:
        """
        创建页面节点。

        页面节点只能在应用节点下创建。

        参数:
            project_id: 项目 ID
            parent_id: 父节点 ID（必须是应用节点）
            name: 节点名称
            description: 节点描述
            creator: 创建者用户 ID

        返回:
            ProjectNode: 创建后的节点

        异常:
            ValueError: 当父节点不是应用节点时抛出
        """
        # 获取父节点
        parent = await self._node_port.get_node_by_id(parent_id)
        
        # 验证父节点类型
        if parent.node_type != NodeType.APPLICATION:
            raise ValueError("页面节点只能在应用节点下创建")
        
        # 获取排序值
        max_sort = await self._node_port.get_max_sort(parent_id, project_id)
        
        node = ProjectNode(
            id=0,
            project_id=project_id,
            node_type=NodeType.PAGE,
            name=name,
            parent_id=parent_id,
            description=description,
            sort=max_sort + 1,
            creator=creator,
        )
        node.validate()
        node.validate_parent(parent)
        
        return await self._node_port.create_node(node)

    async def create_function_node(
        self,
        project_id: int,
        parent_id: int,
        name: str,
        description: Optional[str] = None,
        creator: int = 0,
    ) -> ProjectNode:
        """
        创建功能节点。

        功能节点只能在页面节点下创建，创建时自动创建关联的功能设计文档。

        参数:
            project_id: 项目 ID
            parent_id: 父节点 ID（必须是页面节点）
            name: 节点名称
            description: 节点描述
            creator: 创建者用户 ID

        返回:
            ProjectNode: 创建后的节点

        异常:
            ValueError: 当父节点不是页面节点时抛出
        """
        # 获取父节点
        parent = await self._node_port.get_node_by_id(parent_id)
        
        # 验证父节点类型
        if parent.node_type != NodeType.PAGE:
            raise ValueError("功能节点只能在页面节点下创建")
        
        # 获取排序值
        max_sort = await self._node_port.get_max_sort(parent_id, project_id)
        
        node = ProjectNode(
            id=0,
            project_id=project_id,
            node_type=NodeType.FUNCTION,
            name=name,
            parent_id=parent_id,
            description=description,
            sort=max_sort + 1,
            creator=creator,
        )
        node.validate()
        node.validate_parent(parent)
        
        # 创建节点
        node = await self._node_port.create_node(node)
        
        # 自动创建功能设计文档、初始化为空 {} 并回写 document_id 到节点
        if self._document_port:
            document = FunctionDocument(
                id=0,
                function_node_id=node.id,
                creator=creator,
            )
            await self._document_port.create_document(document)
            if self._document_content_port:
                await self._document_content_port.set_content(document.id, {})
            await self._node_port.update_node_document_id(node.id, document.id)
            node.document_id = document.id
            logger.info(f"自动创建功能设计文档并初始化: node_id={node.id}, document_id={document.id}")
        
        return node

    async def update_node(
        self,
        node_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        editor: int = 0,
    ) -> ProjectNode:
        """
        更新节点信息。

        参数:
            node_id: 节点 ID
            name: 新的节点名称
            description: 新的节点描述
            editor: 编辑者用户 ID

        返回:
            ProjectNode: 更新后的节点

        异常:
            ValueError: 当节点不存在或处于开发模式时抛出
        """
        # 获取节点
        node = await self._node_port.get_node_by_id(node_id)
        
        # 更新字段
        node.update(name=name, description=description, editor=editor)
        node.validate()
        
        return await self._node_port.update_node(node)

    async def move_node(
        self,
        node_id: int,
        new_parent_id: Optional[int],
        predecessor_node_id: Optional[int] = None,
        editor: int = 0,
    ) -> ProjectNode:
        """
        移动节点到新的父节点下。

        参数:
            node_id: 节点 ID
            new_parent_id: 新父节点 ID
            predecessor_node_id: 前置节点 ID（新父节点下的直接子节点，移动后位于该节点之后）；
                None 表示放到第一个
            editor: 编辑者用户 ID

        返回:
            ProjectNode: 移动后的节点

        异常:
            ValueError: 当移动违反层级约束或有开发模式节点时抛出
        """
        # 获取节点
        node = await self._node_port.get_node_by_id(node_id)
        if predecessor_node_id is not None and predecessor_node_id == node_id:
            raise ValueError("前置节点不能为当前被移动的节点")

        # 验证新父节点
        new_parent = None
        if new_parent_id:
            new_parent = await self._node_port.get_node_by_id(new_parent_id)
            node.validate_parent(new_parent)
            if new_parent.path.startswith(node.path):
                raise ValueError("不能将节点移动到其子节点下")
        else:
            if node.node_type != NodeType.APPLICATION:
                raise ValueError(f"{node.node_type.value} 节点必须有父节点")

        # 根据前置节点计算 new_sort 并重设入库
        if predecessor_node_id is None:
            new_sort = 0
        else:
            predecessor = await self._node_port.get_node_by_id(predecessor_node_id)
            if predecessor.parent_id != new_parent_id:
                raise ValueError("前置节点必须为新父节点下的直接子节点")
            if predecessor.project_id != node.project_id:
                raise ValueError("前置节点须属于同一项目")
            new_sort = predecessor.sort + 1

        return await self._node_port.move_node(node_id, new_parent_id, new_sort)

    async def delete_node(self, node_id: int) -> bool:
        """
        删除节点。

        参数:
            node_id: 节点 ID

        返回:
            bool: 是否删除成功

        异常:
            ValueError: 当节点有子节点、处于开发模式或不存在时抛出
        """
        # 获取节点
        node = await self._node_port.get_node_by_id(node_id)
        
        # 检查是否有子节点
        if await self._node_port.has_children(node_id):
            raise ValueError("节点存在子节点，请先删除或移动子节点")
        
        # 若是功能节点，删除关联的文档内容、文档块和文档元信息
        if node.node_type == NodeType.FUNCTION and self._document_port:
            document = await self._document_port.get_document_by_node_id(node_id)
            if document:
                if self._document_content_port:
                    await self._document_content_port.delete_content(document.id)
                if self._document_block_port:
                    await self._document_block_port.delete_blocks_by_document_id(document.id)
                await self._document_port.delete_document_by_node_id(node_id)
        
        return await self._node_port.delete_node(node_id)

    async def get_application_detail_for_mcp(self, node_id: int) -> dict:
        """
        获取应用详情供 MCP Server 使用（内部接口，无认证）。

        - 待开发内容：入参节点及其所有后代节点，以及各自关联的文档内容（若有）。
        - 背景 Context：入参节点的父节点链直至根节点，以及各自关联的文档内容（若有）。

        参数:
            node_id: 节点 ID（URL 所代表的节点）

        返回:
            dict: {"context": [...], "content_to_develop": [...]}
            每项为 {"node": {...}, "document": TipTap JSON | null, "document_text": 可读文本 | null}，
            document_text 供 Coding Agent 直接使用。
        """
        node = await self._node_port.get_node_by_id(node_id)

        def node_to_info(n: ProjectNode) -> dict:
            return {
                "id": n.id,
                "project_id": n.project_id,
                "parent_id": n.parent_id,
                "node_type": n.node_type.value,
                "name": n.name,
                "description": n.description,
                "path": n.path,
                "sort": n.sort,
                "document_id": n.document_id,
            }

        async def doc_for_node(n: ProjectNode):
            if n.document_id and self._document_content_port:
                return await self._document_content_port.get_content(n.document_id)
            return None

        def item_with_doc(node_info: dict, doc: Optional[dict]) -> dict:
            out = {"node": node_info, "document": doc}
            out["document_text"] = tiptap_json_to_readable_text(doc) if doc else None
            return out

        # 祖先链：从父节点到根节点（顺序：根 -> ... -> 直接父节点）
        ancestors: List[ProjectNode] = []
        current_id = node.parent_id
        while current_id is not None:
            anc = await self._node_port.get_node_by_id_optional(current_id)
            if anc is None:
                break
            ancestors.append(anc)
            current_id = anc.parent_id
        ancestors.reverse()

        context = []
        for anc in ancestors:
            doc = await doc_for_node(anc)
            context.append(item_with_doc(node_to_info(anc), doc))

        # 待开发内容：当前节点 + 所有后代
        descendants = await self._node_port.get_descendants(node_id)
        content_to_develop = []
        for n in [node] + descendants:
            doc = await doc_for_node(n)
            content_to_develop.append(item_with_doc(node_to_info(n), doc))

        return {"context": context, "content_to_develop": content_to_develop}
