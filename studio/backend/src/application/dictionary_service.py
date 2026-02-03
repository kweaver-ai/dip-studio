"""
项目词典服务

应用层服务，负责编排项目词典管理操作。
"""
import logging
from typing import List, Optional

from src.domains.dictionary import DictionaryEntry
from src.ports.dictionary_port import DictionaryPort
from src.ports.project_port import ProjectPort

logger = logging.getLogger(__name__)


class DictionaryService:
    """
    项目词典服务。

    该服务属于应用层，通过端口编排词典管理的业务逻辑。
    """

    def __init__(
        self,
        dictionary_port: DictionaryPort,
        project_port: Optional[ProjectPort] = None,
    ):
        """
        初始化词典服务。

        参数:
            dictionary_port: 词典端口实现
            project_port: 项目端口实现（用于验证项目存在）
        """
        self._dictionary_port = dictionary_port
        self._project_port = project_port

    async def get_entries_by_project_id(self, project_id: int) -> List[DictionaryEntry]:
        """
        获取项目的所有词典条目。

        参数:
            project_id: 项目 ID

        返回:
            List[DictionaryEntry]: 词典条目列表
        """
        return await self._dictionary_port.get_entries_by_project_id(project_id)

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
        return await self._dictionary_port.get_entry_by_id(entry_id)

    async def create_entry(
        self,
        project_id: int,
        term: str,
        definition: str,
    ) -> DictionaryEntry:
        """
        创建新的词典条目。

        参数:
            project_id: 项目 ID
            term: 术语名称
            definition: 术语定义

        返回:
            DictionaryEntry: 创建后的词典条目

        异常:
            ValueError: 当术语已存在或数据验证失败时抛出
        """
        # 验证项目存在
        if self._project_port:
            await self._project_port.get_project_by_id(project_id)
        
        entry = DictionaryEntry(
            id=0,
            project_id=project_id,
            term=term,
            definition=definition,
        )
        entry.validate()
        
        return await self._dictionary_port.create_entry(entry)

    async def update_entry(
        self,
        entry_id: int,
        term: Optional[str] = None,
        definition: Optional[str] = None,
    ) -> DictionaryEntry:
        """
        更新词典条目。

        参数:
            entry_id: 条目 ID
            term: 新的术语名称
            definition: 新的术语定义

        返回:
            DictionaryEntry: 更新后的词典条目

        异常:
            ValueError: 当条目不存在或术语已存在时抛出
        """
        # 获取现有条目
        entry = await self._dictionary_port.get_entry_by_id(entry_id)
        
        # 更新字段
        entry.update(term=term, definition=definition)
        entry.validate()
        
        return await self._dictionary_port.update_entry(entry)

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
        return await self._dictionary_port.delete_entry(entry_id)

    async def check_term_available(
        self,
        project_id: int,
        term: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """
        检查术语是否可用。

        参数:
            project_id: 项目 ID
            term: 术语名称
            exclude_id: 排除的条目 ID（用于更新时检查）

        返回:
            bool: 是否可用
        """
        exists = await self._dictionary_port.check_term_exists(project_id, term, exclude_id)
        return not exists
