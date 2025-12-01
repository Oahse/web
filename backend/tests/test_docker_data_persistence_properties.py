"""
Property-based tests for Docker data persistence across container restarts.

**Feature: app-enhancements, Property 65: Data persistence across restarts**
**Validates: Requirements 19.6**
"""

import pytest
import asyncio
import uuid
import subprocess
import time
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select
from core.config import settings
from models.user import User
from models.product import Category
from core.utils.encryption import PasswordManager


def is_docker_running():
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def are_containers_running():
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = subprocess.run(
            ["docker", "compose", "ps", "--services", "--filter", "status=running"],
            capture_output=True, text=True, timeout=10, cwd=project_root
        )
        services = [s for s in result.stdout.strip().split('\n') if s.strip()]
        return len(services) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def restart_containers():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        print("Stopping containers...")
        subprocess.run(["docker", "compose", "stop"], capture_output=True, timeout=60, cwd=project_root, check=True)
        time.sleep(3)
        print("Starting containers...")
        subprocess.run(["docker", "compose", "start"], capture_output=True, timeout=60, cwd=project_root, check=True)
        print("Waiting for database...")
        time.sleep(15)
        return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Restart failed: {e}")
        return False


async def wait_for_database(max_attempts=10):
    for attempt in range(max_attempts):
        try:
            engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False, pool_pre_ping=True)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            return True
        except Exception:
            if attempt < max_attempts - 1:
                await asyncio.sleep(2)
    return False


@pytest.mark.asyncio
@pytest.mark.skipif(not is_docker_running(), reason="Docker not running")
@pytest.mark.skipif(not are_containers_running(), reason="Containers not running")
async def test_user_data_persists_across_container_restart():
    """Property: User data persists when containers are stopped and restarted."""
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False, pool_pre_ping=True)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    user_id = None
    test_email = f"restart_test_{uuid.uuid4()}@example.com"
    
    try:
        # Create user
        async with async_session_maker() as session:
            pm = PasswordManager()
            user = User(
                email=test_email, firstname="Restart", lastname="Test",
                hashed_password=pm.hash_password("testpassword123"),
                role="Customer", verified=True, active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            user_id = user.id
        
        await engine.dispose()
        
        # Restart containers
        assert restart_containers(), "Failed to restart containers"
        assert await wait_for_database(), "Database not accessible after restart"
        
        # Verify user persists
        engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False, pool_pre_ping=True)
        async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session_maker() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            retrieved_user = result.scalar_one_or_none()
            assert retrieved_user is not None, "User should persist across container restarts"
            assert retrieved_user.email == test_email
        
        # Cleanup
        async with async_session_maker() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user_to_delete = result.scalar_one_or_none()
            if user_to_delete:
                await session.delete(user_to_delete)
                await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_docker_environment_check():
    """Helper test to verify Docker environment."""
    if not is_docker_running():
        pytest.skip("Docker daemon not running")
    if not are_containers_running():
        pytest.skip("Docker containers not running. Run: docker compose up -d")
    print("✓ Docker environment ready")
