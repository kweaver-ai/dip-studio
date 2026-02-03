"""
项目词典端口接口

定义项目词典操作的抽象接口（端口）。
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domains.dictionary import DictionaryEntry


class DictionaryPort(ABC):
    """
    项目词典端口接口。

    这是一个输出端口（被驱动端口），定义了应用程序与外部词典数据存储的交互方式。
    """

    @abstractmethod
    async def get_entries_by_project_id(self, project_id: int) -> List[DictionaryEntry]:
        """
        获取项目的所有词典条目。

        参数:
            project_id: 项目 ID

        返回:
            List[DictionaryEntry]: 词典条目列表
        """
        pass

    @abstractmethod
    async def get_entry_by_id(self, entry_id: int) -> DictionaryEntry:
        """
        根据条目 ID 获取词典条目。

        参数:
            entry_id: 条目 ID

        返回:
            DictionaryEntry: 词典条目

        异常:
            ValueError: 当条目不存在时抛出
        """
        pass

    @abstractmethod
    async def get_entry_by_id_optional(self, entry_id: int) -> Optional[DictionaryEntry]:
        """
        根据条目 ID 获取词典条目（可选）。

        参数:
            entry_id: 条目 ID

        返回:
            Optional[DictionaryEntry]: 词典条目，不存在时返回 None
        """
        pass

    @abstractmethod
    async def get_entry_by_term(self, project_id: int, term: str) -> Optional[DictionaryEntry]:
        """
        根据术语名称获取词典条目。

        参数:
            project_id: 项目 ID
            term: 术语名称

        返回:
            Optional[DictionaryEntry]: 词典条目，不存在时返回 None
        """
        pass

    @abstractmethod
    async def create_entry(self, entry: DictionaryEntry) -> DictionaryEntry:
        """
        创建新的词典条目。

        参数:
            entry: 词典条目

        返回:
            DictionaryEntry: 创建后的词典条目（包含生成的 ID）

        异常:
            ValueError: 当术语在项目中已存在时抛出
        """
        pass

    @abstractmethod
    async def update_entry(self, entry: DictionaryEntry) -> DictionaryEntry:
        """
        更新词典条目。

        参数:
            entry: 词典条目

        返回:
            DictionaryEntry: 更新后的词典条目

        异常:
            ValueError: 当条目不存在时抛出
        """
        pass

    @abstractmethod
    async def delete_entry(self, entry_id: int) -> bool:
        """
        删除词典条目。

        参数:
            entry_id: 条目 ID

        返回:
            bool: 是否删除成功

        异常:
            ValueError: 当条目不存在时抛出
        """
        pass

    @abstractmethod
    async def delete_entries_by_project_id(self, project_id: int) -> int:
        """
        删除项目的所有词典条目。

        参数:
            project_id: 项目 ID

        返回:
            int: 删除的条目数量
        """
        pass

    @abstractmethod
    async def check_term_exists(
        self,
        project_id: int,
        term: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """
        检查术语在项目中是否已存在。

        参数:
            project_id: 项目 ID
            term: 术语名称
            exclude_id: 排除的条目 ID（用于更新时检查）

        返回:
            bool: 是否存在
        """
        pass
