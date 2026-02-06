"""
节点 API 集成测试

注意：这些测试需要数据库连接，在 CI 环境中可能需要跳过。
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要数据库连接")
async def test_create_application_node(client: AsyncClient):
    """测试创建应用节点接口。"""
    # 先创建项目
    project_response = await client.post(
        "/api/dip-studio/v1/projects",
        json={"name": "测试项目"}
    )
    project_id = project_response.json()["id"]
    
    # 创建应用节点
    response = await client.post(
        "/api/dip-studio/v1/nodes/application",
        json={
            "project_id": project_id,
            "name": "测试应用",
            "description": "这是一个测试应用",
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data["id"], str) and len(data["id"]) == 36, "节点 ID 应为 UUID 字符串"
    assert data["name"] == "测试应用"
    assert data["node_type"] == "application"
    assert data["parent_id"] is None


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要数据库连接")
async def test_create_page_node(client: AsyncClient):
    """测试创建页面节点接口。"""
    # 先创建项目和应用节点
    project_response = await client.post(
        "/api/dip-studio/v1/projects",
        json={"name": "测试项目2"}
    )
    project_id = project_response.json()["id"]
    
    app_response = await client.post(
        "/api/dip-studio/v1/nodes/application",
        json={"project_id": project_id, "name": "测试应用"}
    )
    app_id = app_response.json()["id"]
    
    # 创建页面节点
    response = await client.post(
        "/api/dip-studio/v1/nodes/page",
        json={
            "project_id": project_id,
            "parent_id": app_id,
            "name": "测试页面",
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试页面"
    assert data["node_type"] == "page"
    assert data["parent_id"] == app_id


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要数据库连接")
async def test_create_function_node(client: AsyncClient):
    """测试创建功能节点接口。"""
    # 先创建项目、应用节点和页面节点
    project_response = await client.post(
        "/api/dip-studio/v1/projects",
        json={"name": "测试项目3"}
    )
    project_id = project_response.json()["id"]
    
    app_response = await client.post(
        "/api/dip-studio/v1/nodes/application",
        json={"project_id": project_id, "name": "测试应用"}
    )
    app_id = app_response.json()["id"]
    
    page_response = await client.post(
        "/api/dip-studio/v1/nodes/page",
        json={"project_id": project_id, "parent_id": app_id, "name": "测试页面"}
    )
    page_id = page_response.json()["id"]
    
    # 创建功能节点
    response = await client.post(
        "/api/dip-studio/v1/nodes/function",
        json={
            "project_id": project_id,
            "parent_id": page_id,
            "name": "测试功能",
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试功能"
    assert data["node_type"] == "function"
    assert data["parent_id"] == page_id


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要数据库连接")
async def test_get_node_tree(client: AsyncClient):
    """测试获取节点树接口。"""
    # 先创建项目和节点结构
    project_response = await client.post(
        "/api/dip-studio/v1/projects",
        json={"name": "测试项目4"}
    )
    project_id = project_response.json()["id"]
    
    await client.post(
        "/api/dip-studio/v1/nodes/application",
        json={"project_id": project_id, "name": "测试应用"}
    )
    
    # 获取节点树
    response = await client.get(f"/api/dip-studio/v1/projects/{project_id}/nodes/tree")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试应用"
    assert data["node_type"] == "application"
    assert "children" in data


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要数据库连接")
async def test_delete_node_with_children(client: AsyncClient):
    """测试删除有子节点的节点。"""
    # 创建项目和节点结构
    project_response = await client.post(
        "/api/dip-studio/v1/projects",
        json={"name": "测试项目5"}
    )
    project_id = project_response.json()["id"]
    
    app_response = await client.post(
        "/api/dip-studio/v1/nodes/application",
        json={"project_id": project_id, "name": "测试应用"}
    )
    app_id = app_response.json()["id"]
    
    await client.post(
        "/api/dip-studio/v1/nodes/page",
        json={"project_id": project_id, "parent_id": app_id, "name": "测试页面"}
    )
    
    # 尝试删除有子节点的应用节点
    response = await client.delete(f"/api/dip-studio/v1/nodes/{app_id}")
    
    assert response.status_code == 400
    data = response.json()
    assert "子节点" in data["description"]
