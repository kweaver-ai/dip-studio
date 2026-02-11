"""
项目服务

应用层服务，负责编排项目管理操作。
"""
import logging
from typing import List, Optional

from src.domains.project import Project
from src.domains.node import NodeType
from src.infrastructure.context import get_user_id
from src.ports.project_port import ProjectPort
from src.ports.node_port import NodePort
from src.ports.dictionary_port import DictionaryPort
from src.ports.document_port import (
    DocumentPort,
    DocumentBlockPort,
    DocumentContentPort,
)

logger = logging.getLogger(__name__)


class ProjectService:
    """
    项目服务。

    该服务属于应用层，通过端口编排项目管理的业务逻辑。
    """

    def __init__(
        self,
        project_port: ProjectPort,
        node_port: Optional[NodePort] = None,
        dictionary_port: Optional[DictionaryPort] = None,
        document_port: Optional[DocumentPort] = None,
        document_block_port: Optional[DocumentBlockPort] = None,
        document_content_port: Optional[DocumentContentPort] = None,
    ):
        """
        初始化项目服务。

        参数:
            project_port: 项目端口实现
            node_port: 节点端口实现（用于级联删除）
            dictionary_port: 词典端口实现（用于级联删除）
            document_port: 文档端口实现（用于删除功能文档元信息）
            document_block_port: 文档块端口实现（用于删除文档块）
            document_content_port: 文档内容端口实现（用于删除文档内容）
        """
        self._project_port = project_port
        self._node_port = node_port
        self._dictionary_port = dictionary_port
        self._document_port = document_port
        self._document_block_port = document_block_port
        self._document_content_port = document_content_port

    async def get_all_projects(self) -> List[Project]:
        """
        获取当前用户创建的项目列表。

        从上下文中取当前用户 ID，仅返回创建人为当前用户的项目。

        返回:
            List[Project]: 项目列表
        """
        creator_id = get_user_id()
        return await self._project_port.get_all_projects(creator_id=creator_id)

    async def get_project_by_id(self, project_id: int) -> Project:
        """
        根据项目 ID 获取项目信息。

        参数:
            project_id: 项目主键 ID

        返回:
            Project: 项目实体

        异常:
            ValueError: 当项目不存在时抛出
        """
        return await self._project_port.get_project_by_id(project_id)

    async def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        creator_id: str = "",
        creator_name: str = "",
    ) -> Project:
        """
        创建新项目。

        参数:
            name: 项目名称
            description: 项目描述
            creator_id: 创建者用户 ID（UUID 字符串）
            creator_name: 创建者用户显示名

        返回:
            Project: 创建后的项目实体

        异常:
            ValueError: 当项目名称已存在或数据验证失败时抛出
        """
        project = Project(
            id=0,
            name=name,
            description=description,
            creator_id=creator_id,
            creator_name=creator_name,
        )
        project.validate()
        
        return await self._project_port.create_project(project)

    async def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        editor_id: str = "",
        editor_name: str = "",
    ) -> Project:
        """
        更新项目信息。

        参数:
            project_id: 项目主键 ID
            name: 新的项目名称
            description: 新的项目描述
            editor_id: 编辑者用户 ID（UUID 字符串）
            editor_name: 编辑者用户显示名

        返回:
            Project: 更新后的项目实体

        异常:
            ValueError: 当项目不存在或数据验证失败时抛出
        """
        # 获取现有项目
        project = await self._project_port.get_project_by_id(project_id)

        # 更新字段
        project.update(
            name=name,
            description=description,
            editor_id=editor_id,
            editor_name=editor_name,
        )
        project.validate()
        
        return await self._project_port.update_project(project)

    async def delete_project(self, project_id: int) -> bool:
        """
        删除项目及其下的所有内容（节点、文档、词典）。

        参数:
            project_id: 项目主键 ID

        返回:
            bool: 是否删除成功

        异常:
            ValueError: 当项目不存在时抛出
        """
        # 获取项目信息（验证项目存在）
        await self._project_port.get_project_by_id(project_id)

        # 1. 删除项目下所有节点及其关联的功能文档（内容 + 块 + 元信息）
        if self._node_port:
            nodes = await self._node_port.get_nodes_by_project_id(project_id)

            # 先删除功能节点关联的文档，避免遗留孤立数据
            if nodes and self._document_port:
                for node in nodes:
                    if (
                        node.node_type == NodeType.FUNCTION
                        and node.document_id is not None
                    ):
                        document_id = node.document_id
                        # 删除文档内容（单 JSON 对象）
                        if self._document_content_port:
                            await self._document_content_port.delete_content(document_id)
                        # 删除文档块
                        if self._document_block_port:
                            await self._document_block_port.delete_blocks_by_document_id(
                                document_id
                            )
                        # 删除文档元信息
                        await self._document_port.delete_document(document_id)

            # 然后删除项目下所有节点（无需逐个检查子节点）
            await self._node_port.delete_nodes_by_project_id(project_id)

        # 2. 删除项目词典
        if self._dictionary_port:
            await self._dictionary_port.delete_entries_by_project_id(project_id)

        # 3. 删除项目本身
        return await self._project_port.delete_project(project_id)

    async def check_name_available(
        self,
        name: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """
        检查项目名称是否可用。

        参数:
            name: 项目名称
            exclude_id: 排除的项目 ID（用于更新时检查）

        返回:
            bool: 是否可用
        """
        exists = await self._project_port.check_name_exists(name, exclude_id)
        return not exists
