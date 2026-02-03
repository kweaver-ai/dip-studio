"""
领域模型单元测试
"""
import pytest
from datetime import datetime

from src.domains.project import Project
from src.domains.node import ProjectNode, NodeType
from src.domains.dictionary import DictionaryEntry
from src.domains.document import FunctionDocument, DocumentBlock, BlockType


class TestProject:
    """项目领域模型测试。"""
    
    def test_create_project(self):
        """测试创建项目。"""
        project = Project(
            id=1,
            name="测试项目",
            description="这是一个测试项目",
            creator=100,
        )
        
        assert project.id == 1
        assert project.name == "测试项目"
        assert project.description == "这是一个测试项目"
        assert project.creator == 100
        assert project.editor == 100
        assert project.created_at is not None
        assert project.edited_at is not None
    
    def test_validate_project_name_empty(self):
        """测试项目名称为空时的验证。"""
        project = Project(id=1, name="", creator=100)
        with pytest.raises(ValueError, match="项目名称"):
            project.validate()
    
    def test_validate_project_name_too_long(self):
        """测试项目名称过长时的验证。"""
        project = Project(id=1, name="a" * 129, creator=100)
        with pytest.raises(ValueError, match="项目名称"):
            project.validate()
    
    def test_validate_project_description_too_long(self):
        """测试项目描述过长时的验证。"""
        project = Project(id=1, name="测试", description="a" * 401, creator=100)
        with pytest.raises(ValueError, match="项目描述"):
            project.validate()
    
    def test_update_project(self):
        """测试更新项目。"""
        project = Project(id=1, name="原始名称", creator=100)
        project.update(name="新名称", description="新描述", editor=200)
        
        assert project.name == "新名称"
        assert project.description == "新描述"
        assert project.editor == 200


class TestProjectNode:
    """项目节点领域模型测试。"""
    
    def test_create_application_node(self):
        """测试创建应用节点。"""
        node = ProjectNode(
            id=1,
            project_id=1,
            node_type=NodeType.APPLICATION,
            name="测试应用",
            creator=100,
        )
        
        assert node.id == 1
        assert node.node_type == NodeType.APPLICATION
        assert node.parent_id is None
        assert node.can_have_children()
    
    def test_create_function_node_cannot_have_children(self):
        """测试功能节点不能有子节点。"""
        node = ProjectNode(
            id=1,
            project_id=1,
            node_type=NodeType.FUNCTION,
            name="测试功能",
            parent_id=2,
            creator=100,
        )
        
        assert not node.can_have_children()
    
    def test_validate_parent_application(self):
        """测试应用节点不能有父节点。"""
        node = ProjectNode(
            id=1,
            project_id=1,
            node_type=NodeType.APPLICATION,
            name="测试",
            creator=100,
        )
        
        # 应用节点验证 None 父节点应该通过
        node.validate_parent(None)
    
    def test_validate_parent_page_requires_application(self):
        """测试页面节点必须在应用节点下。"""
        page = ProjectNode(
            id=2,
            project_id=1,
            node_type=NodeType.PAGE,
            name="测试页面",
            parent_id=1,
            creator=100,
        )
        
        # 父节点是应用节点
        app = ProjectNode(
            id=1,
            project_id=1,
            node_type=NodeType.APPLICATION,
            name="测试应用",
            creator=100,
        )
        
        page.validate_parent(app)  # 应该通过
    
    def test_validate_parent_page_invalid(self):
        """测试页面节点在错误父节点下的验证。"""
        page = ProjectNode(
            id=2,
            project_id=1,
            node_type=NodeType.PAGE,
            name="测试页面",
            parent_id=1,
            creator=100,
        )
        
        # 父节点是功能节点（错误）
        func = ProjectNode(
            id=1,
            project_id=1,
            node_type=NodeType.FUNCTION,
            name="测试功能",
            parent_id=3,
            creator=100,
        )
        
        with pytest.raises(ValueError):
            page.validate_parent(func)
    
    def test_build_path(self):
        """测试构建节点路径。"""
        node = ProjectNode(
            id=5,
            project_id=1,
            node_type=NodeType.PAGE,
            name="测试",
            creator=100,
        )
        
        path = node.build_path("/node_1")
        assert path == "/node_1/node_5"


class TestDictionaryEntry:
    """词典条目领域模型测试。"""
    
    def test_create_entry(self):
        """测试创建词典条目。"""
        entry = DictionaryEntry(
            id=1,
            project_id=1,
            term="ROI",
            definition="投资回报率",
        )
        
        assert entry.term == "ROI"
        assert entry.definition == "投资回报率"
    
    def test_validate_term_empty(self):
        """测试术语为空时的验证。"""
        entry = DictionaryEntry(id=1, project_id=1, term="", definition="定义")
        with pytest.raises(ValueError, match="术语"):
            entry.validate()
    
    def test_validate_definition_empty(self):
        """测试定义为空时的验证。"""
        entry = DictionaryEntry(id=1, project_id=1, term="术语", definition="")
        with pytest.raises(ValueError, match="定义"):
            entry.validate()


class TestDocumentBlock:
    """文档块领域模型测试。"""
    
    def test_create_block(self):
        """测试创建文档块。"""
        block = DocumentBlock(
            id="abc123",
            document_id=1,
            type=BlockType.TEXT,
            content={"text": "Hello"},
            order=1,
        )
        
        assert block.type == BlockType.TEXT
        assert block.content == {"text": "Hello"}
