"""
项目服务

应用层服务，负责编排项目管理操作。
"""
import logging
from typing import List, Optional

from src.domains.project import Project
from src.ports.project_port import ProjectPort
from src.ports.node_port import NodePort
from src.ports.dictionary_port import DictionaryPort

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
    ):
        """
        初始化项目服务。

        参数:
            project_port: 项目端口实现
            node_port: 节点端口实现（用于级联删除）
            dictionary_port: 词典端口实现（用于级联删除）
        """
        self._project_port = project_port
        self._node_port = node_port
        self._dictionary_port = dictionary_port

    async def get_all_projects(self) -> List[Project]:
        """
        获取所有项目列表。

        返回:
            List[Project]: 项目列表
        """
        return await self._project_port.get_all_projects()

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
        creator: int = 0,
    ) -> Project:
        """
        创建新项目。

        参数:
            name: 项目名称
            description: 项目描述
            creator: 创建者用户 ID

        返回:
            Project: 创建后的项目实体

        异常:
            ValueError: 当项目名称已存在或数据验证失败时抛出
        """
        project = Project(
            id=0,
            name=name,
            description=description,
            creator=creator,
        )
        project.validate()
        
        return await self._project_port.create_project(project)

    async def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        editor: int = 0,
    ) -> Project:
        """
        更新项目信息。

        参数:
            project_id: 项目主键 ID
            name: 新的项目名称
            description: 新的项目描述
            editor: 编辑者用户 ID

        返回:
            Project: 更新后的项目实体

        异常:
            ValueError: 当项目不存在或数据验证失败时抛出
        """
        # 获取现有项目
        project = await self._project_port.get_project_by_id(project_id)
        
        # 更新字段
        project.update(name=name, description=description, editor=editor)
        project.validate()
        
        return await self._project_port.update_project(project)

    async def delete_project(self, project_id: int) -> bool:
        """
        删除项目。

        参数:
            project_id: 项目主键 ID

        返回:
            bool: 是否删除成功

        异常:
            ValueError: 当项目不存在或有节点时抛出
        """
        # 获取项目信息（验证项目存在）
        await self._project_port.get_project_by_id(project_id)
        
        if self._node_port:
            # 检查是否有节点
            nodes = await self._node_port.get_nodes_by_project_id(project_id)
            if nodes:
                raise ValueError("项目存在节点，请先删除项目节点")
        
        # 删除项目词典
        if self._dictionary_port:
            await self._dictionary_port.delete_entries_by_project_id(project_id)
        
        # 删除项目
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
