import pytest
import asyncio
from typing import AsyncGenerator

from fastapi.testclient import TestClient
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app
from core.database import get_db, Base

# Use PostgreSQL in Docker for testing
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://banwee:banwee_password@localhost:5432/banwee_db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    poolclass=None  # Disable pooling for tests to avoid connection issues
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)

Base.metadata.bind = engine

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function", autouse=True)
async def db_setup_and_teardown():
    """Setup and teardown database for each test function."""
    # Don't create/drop tables for every test - too slow
    # Instead, just ensure tables exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass  # Tables might already exist
    yield
    # Don't drop tables after each test - causes issues with concurrent tests

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
    from core.utils.auth.jwt_auth import JWTManager
    from uuid import uuid4
    import bcrypt
    
    # Store email before creating user
    test_email = "test@example.com"
    
    # Create a test supplier user
    test_user = User(
        id=uuid4(),
        email=test_email,
        firstname="Test",
        lastname="User",
        role="Supplier",
        active=True,
        verified=True,
        hashed_password=bcrypt.hashpw("testpassword123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    )
    
    db_session.add(test_user)
    await db_session.commit()
    
    # Create access token using stored email
    jwt_manager = JWTManager()
    access_token = jwt_manager.create_access_token(data={"sub": test_email})
    
    return {"Authorization": f"Bearer {access_token}"}
