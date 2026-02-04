"""
依赖注入容器

按照六边形架构组装和连接所有依赖。
在这里实例化适配器并注入到应用服务中。
"""
import logging

from src.application.project_service import ProjectService
from src.application.node_service import NodeService
from src.application.dictionary_service import DictionaryService
from src.application.document_service import DocumentService
from src.adapters.project_adapter import ProjectAdapter
from src.adapters.node_adapter import NodeAdapter
from src.adapters.dictionary_adapter import DictionaryAdapter
from src.adapters.document_adapter import DocumentAdapter
from src.adapters.document_block_adapter import DocumentBlockAdapter
from src.adapters.document_content_adapter import DocumentContentAdapter
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.database.mariadb import MariaDBPool

logger = logging.getLogger(__name__)


class Container:
    """
    依赖注入容器。
    
    该容器负责组装所有依赖，并提供工厂方法来创建带有适配器的应用服务。
    """
    
    def __init__(self, settings: Settings = None):
        """
        初始化容器。

        参数:
            settings: 应用配置。如果为 None，则使用默认配置。
        """
        self._settings = settings or get_settings()
        
        # 数据库连接
        self._mariadb_pool: MariaDBPool = None
        
        # 适配器
        self._project_adapter: ProjectAdapter = None
        self._node_adapter: NodeAdapter = None
        self._dictionary_adapter: DictionaryAdapter = None
        self._document_adapter: DocumentAdapter = None
        self._document_block_adapter: DocumentBlockAdapter = None
        self._document_content_adapter: DocumentContentAdapter = None
        
        # 服务
        self._project_service: ProjectService = None
        self._node_service: NodeService = None
        self._dictionary_service: DictionaryService = None
        self._document_service: DocumentService = None
        
        # 就绪状态
        self._ready = False
    
    @property
    def settings(self) -> Settings:
        """获取应用配置。"""
        return self._settings
    
    # ============ 数据库连接 ============
    
    @property
    def mariadb_pool(self) -> MariaDBPool:
        """获取 MariaDB 连接池管理器。"""
        if self._mariadb_pool is None:
            self._mariadb_pool = MariaDBPool(self._settings)
        return self._mariadb_pool
    
    # ============ 适配器 ============
    
    @property
    def project_adapter(self) -> ProjectAdapter:
        """获取项目适配器实例。"""
        if self._project_adapter is None:
            self._project_adapter = ProjectAdapter(self.mariadb_pool)
        return self._project_adapter
    
    @property
    def node_adapter(self) -> NodeAdapter:
        """获取节点适配器实例。"""
        if self._node_adapter is None:
            self._node_adapter = NodeAdapter(self.mariadb_pool)
        return self._node_adapter
    
    @property
    def dictionary_adapter(self) -> DictionaryAdapter:
        """获取词典适配器实例。"""
        if self._dictionary_adapter is None:
            self._dictionary_adapter = DictionaryAdapter(self.mariadb_pool)
        return self._dictionary_adapter
    
    @property
    def document_adapter(self) -> DocumentAdapter:
        """获取文档适配器实例。"""
        if self._document_adapter is None:
            self._document_adapter = DocumentAdapter(self.mariadb_pool)
        return self._document_adapter
    
    @property
    def document_block_adapter(self) -> DocumentBlockAdapter:
        """获取文档块适配器实例（MariaDB）。"""
        if self._document_block_adapter is None:
            self._document_block_adapter = DocumentBlockAdapter(self.mariadb_pool)
        return self._document_block_adapter

    @property
    def document_content_adapter(self) -> DocumentContentAdapter:
        """获取文档内容适配器实例（MariaDB，单 JSON 对象存储）。"""
        if self._document_content_adapter is None:
            self._document_content_adapter = DocumentContentAdapter(self.mariadb_pool)
        return self._document_content_adapter
    
    # ============ 服务 ============
    
    @property
    def project_service(self) -> ProjectService:
        """获取项目服务实例。"""
        if self._project_service is None:
            self._project_service = ProjectService(
                project_port=self.project_adapter,
                node_port=self.node_adapter,
                dictionary_port=self.dictionary_adapter,
                document_port=self.document_adapter,
                document_block_port=self.document_block_adapter,
                document_content_port=self.document_content_adapter,
            )
        return self._project_service
    
    @property
    def node_service(self) -> NodeService:
        """获取节点服务实例。"""
        if self._node_service is None:
            self._node_service = NodeService(
                node_port=self.node_adapter,
                project_port=self.project_adapter,
                document_port=self.document_adapter,
                document_block_port=self.document_block_adapter,
                document_content_port=self.document_content_adapter,
            )
        return self._node_service
    
    @property
    def dictionary_service(self) -> DictionaryService:
        """获取词典服务实例。"""
        if self._dictionary_service is None:
            self._dictionary_service = DictionaryService(
                dictionary_port=self.dictionary_adapter,
                project_port=self.project_adapter,
            )
        return self._dictionary_service
    
    @property
    def document_service(self) -> DocumentService:
        """获取文档服务实例。"""
        if self._document_service is None:
            self._document_service = DocumentService(
                document_port=self.document_adapter,
                document_block_port=self.document_block_adapter,
                document_content_port=self.document_content_adapter,
                node_port=self.node_adapter,
            )
        return self._document_service
    
    # ============ 生命周期管理 ============
    
    def set_ready(self, ready: bool = True) -> None:
        """
        设置服务就绪状态。

        参数:
            ready: 服务是否就绪。
        """
        self._ready = ready
    
    def is_ready(self) -> bool:
        """
        检查服务是否就绪。

        返回:
            bool: 是否就绪。
        """
        return self._ready
    
    async def close(self) -> None:
        """
        关闭容器，释放资源。

        关闭数据库连接池等资源。
        """
        if self._mariadb_pool is not None:
            await self._mariadb_pool.close()
        logger.info("容器资源已释放")


# 全局容器实例
_container: Container = None


def get_container() -> Container:
    """
    获取全局容器实例。
    
    返回:
        Container: 容器实例。
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


def init_container(settings: Settings = None) -> Container:
    """
    初始化全局容器。
    
    参数:
        settings: 应用配置。
    
    返回:
        Container: 初始化后的容器。
    """
    global _container
    _container = Container(settings)
    return _container
