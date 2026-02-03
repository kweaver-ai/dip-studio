"""
测试配置和 Fixtures

提供测试所需的 fixtures 和配置。
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from src.main import create_app
from src.infrastructure.config.settings import Settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """创建测试配置。"""
    return Settings(
        app_name="DIP Studio Test",
        app_version="0.1.0-test",
        debug=True,
        db_host="localhost",
        db_port=3306,
        db_name="dip_studio_test",
        db_user="root",
        db_password="",
        use_mock_services=True,
    )


@pytest_asyncio.fixture
async def app(test_settings: Settings):
    """创建测试应用。"""
    app = create_app(test_settings)
    yield app


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
