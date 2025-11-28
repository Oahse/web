import pytest
import asyncio
from typing import AsyncGenerator

from fastapi.testclient import TestClient
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app
from core.database import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base.metadata.bind = engine

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
async def db_setup_and_teardown():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def auth_headers(db_session: AsyncSession) -> dict:
    """Create a test user and return auth headers"""
    from models.user import User
    from core.utils.auth.jwt_auth import create_access_token
    from uuid import uuid4
    
    # Create a test supplier user
    test_user = User(
        id=uuid4(),
        email="test@example.com",
        firstname="Test",
        lastname="User",
        role="Supplier",
        is_active=True,
        is_verified=True
    )
    test_user.set_password("testpassword123")
    
    db_session.add(test_user)
    await db_session.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": test_user.email})
    
    return {"Authorization": f"Bearer {access_token}"}
