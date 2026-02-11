"""
项目端口接口

定义项目操作的抽象接口（端口）。
遵循六边形架构模式，这些端口定义了领域层与基础设施层之间的契约。
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domains.project import Project


class ProjectPort(ABC):
    """
    项目端口接口。

    这是一个输出端口（被驱动端口），定义了应用程序与外部项目数据存储的交互方式。
    """

    @abstractmethod
    async def get_all_projects(self, creator_id: Optional[str] = None) -> List[Project]:
        """
        获取项目列表。

        参数:
            creator_id: 创建人用户 ID，传入时仅返回该创建人的项目；不传则返回全部（兼容旧调用）。

        返回:
            List[Project]: 项目列表
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_project_by_id_optional(self, project_id: int) -> Optional[Project]:
        """
        根据项目 ID 获取项目信息（可选）。

        参数:
            project_id: 项目主键 ID

        返回:
            Optional[Project]: 项目实体，不存在时返回 None
        """
        pass

    @abstractmethod
    async def get_project_by_name(self, name: str) -> Optional[Project]:
        """
        根据项目名称获取项目信息。

        参数:
            name: 项目名称

        返回:
            Optional[Project]: 项目实体，不存在时返回 None
        """
        pass

    @abstractmethod
    async def create_project(self, project: Project) -> Project:
        """
        创建新项目。

        参数:
            project: 项目实体

        返回:
            Project: 创建后的项目实体（包含生成的 ID）

        异常:
            ValueError: 当项目名称已存在时抛出
        """
        pass

    @abstractmethod
    async def update_project(self, project: Project) -> Project:
        """
        更新项目信息。

        参数:
            project: 项目实体

        返回:
            Project: 更新后的项目实体

        异常:
            ValueError: 当项目不存在时抛出
        """
        pass

    @abstractmethod
    async def delete_project(self, project_id: int) -> bool:
        """
        删除项目。

        参数:
            project_id: 项目主键 ID

        返回:
            bool: 是否删除成功

        异常:
            ValueError: 当项目不存在时抛出
        """
        pass

    @abstractmethod
    async def check_name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """
        检查项目名称是否已存在。

        参数:
            name: 项目名称
            exclude_id: 排除的项目 ID（用于更新时检查）

        返回:
            bool: 是否存在
        """
        pass
