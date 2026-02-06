"""
节点端口接口

定义节点操作的抽象接口（端口）。
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domains.node import ProjectNode, NodeType


class NodePort(ABC):
    """
    节点端口接口。

    这是一个输出端口（被驱动端口），定义了应用程序与外部节点数据存储的交互方式。
    """

    @abstractmethod
    async def get_node_by_id(self, node_id: str) -> ProjectNode:
        """
        根据节点 ID 获取节点信息。

        参数:
            node_id: 节点主键 ID (UUID)

        返回:
            ProjectNode: 节点实体

        异常:
            ValueError: 当节点不存在时抛出
        """
        pass

    @abstractmethod
    async def get_node_by_id_optional(self, node_id: str) -> Optional[ProjectNode]:
        """
        根据节点 ID 获取节点信息（可选）。

        参数:
            node_id: 节点主键 ID (UUID)

        返回:
            Optional[ProjectNode]: 节点实体，不存在时返回 None
        """
        pass

    @abstractmethod
    async def get_nodes_by_project_id(self, project_id: int) -> List[ProjectNode]:
        """
        获取项目下的所有节点。

        参数:
            project_id: 项目 ID

        返回:
            List[ProjectNode]: 节点列表
        """
        pass

    @abstractmethod
    async def get_root_node(self, project_id: int) -> Optional[ProjectNode]:
        """
        获取项目的根节点（应用节点）。

        参数:
            project_id: 项目 ID

        返回:
            Optional[ProjectNode]: 根节点，不存在时返回 None
        """
        pass

    @abstractmethod
    async def get_children(self, node_id: str) -> List[ProjectNode]:
        """
        获取节点的直接子节点。

        参数:
            node_id: 父节点 ID (UUID)

        返回:
            List[ProjectNode]: 子节点列表
        """
        pass

    @abstractmethod
    async def get_descendants(self, node_id: str) -> List[ProjectNode]:
        """
        获取节点的所有后代节点。

        参数:
            node_id: 节点 ID (UUID)

        返回:
            List[ProjectNode]: 后代节点列表
        """
        pass

    @abstractmethod
    async def has_children(self, node_id: str) -> bool:
        """
        检查节点是否有子节点。

        参数:
            node_id: 节点 ID (UUID)

        返回:
            bool: 是否有子节点
        """
        pass

    @abstractmethod
    async def create_node(self, node: ProjectNode) -> ProjectNode:
        """
        创建新节点。

        参数:
            node: 节点实体

        返回:
            ProjectNode: 创建后的节点实体（包含生成的 ID）
        """
        pass

    @abstractmethod
    async def update_node(self, node: ProjectNode) -> ProjectNode:
        """
        更新节点信息。

        参数:
            node: 节点实体

        返回:
            ProjectNode: 更新后的节点实体

        异常:
            ValueError: 当节点不存在时抛出
        """
        pass

    @abstractmethod
    async def update_node_document_id(self, node_id: str, document_id: int) -> bool:
        """
        更新功能节点关联的文档 ID。

        参数:
            node_id: 节点 ID (UUID)
            document_id: 文档 ID

        返回:
            bool: 是否更新成功
        """
        pass

    @abstractmethod
    async def update_node_path(self, node_id: str, new_path: str) -> bool:
        """
        更新节点路径。

        参数:
            node_id: 节点 ID (UUID)
            new_path: 新路径

        返回:
            bool: 是否更新成功
        """
        pass

    @abstractmethod
    async def update_descendants_path(
        self,
        node_id: str,
        old_path: str,
        new_path: str,
    ) -> int:
        """
        更新所有后代节点的路径。

        参数:
            node_id: 节点 ID (UUID)
            old_path: 旧路径前缀
            new_path: 新路径前缀

        返回:
            int: 更新的节点数量
        """
        pass

    @abstractmethod
    async def move_node(
        self,
        node_id: str,
        new_parent_id: Optional[str],
        new_sort: int,
        editor_id: str = "",
        editor_name: str = "",
    ) -> ProjectNode:
        """
        移动节点到新的父节点下。

        参数:
            node_id: 节点 ID (UUID)
            new_parent_id: 新父节点 ID (UUID)
            new_sort: 新的排序值
            editor_id: 编辑者用户 ID（UUID 字符串）
            editor_name: 编辑者用户显示名

        返回:
            ProjectNode: 移动后的节点实体

        异常:
            ValueError: 当节点不存在或移动非法时抛出
        """
        pass

    @abstractmethod
    async def delete_node(self, node_id: str) -> bool:
        """
        删除节点。

        参数:
            node_id: 节点 ID (UUID)

        返回:
            bool: 是否删除成功

        异常:
            ValueError: 当节点不存在时抛出
        """
        pass

    @abstractmethod
    async def delete_nodes_by_project_id(self, project_id: int) -> int:
        """
        删除项目下的所有节点。

        参数:
            project_id: 项目 ID

        返回:
            int: 删除的节点数量
        """
        pass

    @abstractmethod
    async def get_max_sort(self, parent_id: Optional[str], project_id: int) -> int:
        """
        获取同级节点的最大排序值。

        参数:
            parent_id: 父节点 ID (UUID)
            project_id: 项目 ID

        返回:
            int: 最大排序值
        """
        pass
