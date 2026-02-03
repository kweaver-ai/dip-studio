"""
健康检查接口测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查接口。"""
    response = await client.get("/api/dip-studio/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_ready_check(client: AsyncClient):
    """测试就绪检查接口。"""
    response = await client.get("/api/dip-studio/v1/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ready"
    assert "version" in data
