"""
项目 API 集成测试

注意：这些测试需要数据库连接，在 CI 环境中可能需要跳过。
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要数据库连接")
async def test_create_project(client: AsyncClient):
    """测试创建项目接口。"""
    response = await client.post(
        "/api/dip-studio/v1/projects",
        json={
            "name": "测试项目",
            "description": "这是一个测试项目",
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试项目"
    assert data["description"] == "这是一个测试项目"
    assert "id" in data


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要数据库连接")
async def test_get_projects(client: AsyncClient):
    """测试获取项目列表接口。"""
    response = await client.get("/api/dip-studio/v1/projects")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要数据库连接")
async def test_create_project_duplicate_name(client: AsyncClient):
    """测试创建重复名称项目。"""
    # 创建第一个项目
    await client.post(
        "/api/dip-studio/v1/projects",
        json={"name": "重复名称项目"}
    )
    
    # 尝试创建同名项目
    response = await client.post(
        "/api/dip-studio/v1/projects",
        json={"name": "重复名称项目"}
    )
    
    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要数据库连接")
async def test_update_project(client: AsyncClient):
    """测试更新项目接口。"""
    # 创建项目
    create_response = await client.post(
        "/api/dip-studio/v1/projects",
        json={"name": "待更新项目"}
    )
    project_id = create_response.json()["id"]
    
    # 更新项目
    response = await client.put(
        f"/api/dip-studio/v1/projects/{project_id}",
        json={
            "name": "已更新项目",
            "description": "已更新描述",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "已更新项目"
    assert data["description"] == "已更新描述"


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要数据库连接")
async def test_delete_project(client: AsyncClient):
    """测试删除项目接口。确认操作由前端完成，后端仅根据 project_id 删除。"""
    # 创建项目
    create_response = await client.post(
        "/api/dip-studio/v1/projects",
        json={"name": "待删除项目"}
    )
    project_id = create_response.json()["id"]
    
    # 删除项目（无需请求体，确认由前端完成）
    response = await client.delete(f"/api/dip-studio/v1/projects/{project_id}")
    
    assert response.status_code == 204
