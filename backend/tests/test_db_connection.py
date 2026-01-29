#!/usr/bin/env python3
"""
Simple script to test database connection and run basic tests
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from models.user import User, UserRole
from core.db import BaseModel
from uuid import uuid4

# Test database URL - formatted for asyncpg
TEST_DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_qI9D0igTcRXw@ep-plain-morning-ah8l56gm-pooler.c-3.us-east-1.aws.neon.tech/neondb?ssl=require"

async def test_database_connection():
    """Test basic database connection and operations"""
    print("🔄 Testing database connection...")
    
    # Create engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=5
    )
    
    # Create session factory
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    try:
        # Test basic connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Create test schema
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS test_schema"))
            await conn.execute(text("SET search_path TO test_schema"))
            print("✅ Test schema created")
            
            # Import all models to register them
            from models import user, product, cart, orders, payments, shipping, tax_rates, inventories
            
            # Create tables
            await conn.run_sync(BaseModel.metadata.create_all)
            print("✅ Tables created successfully")
        
        # Test creating a user
        async with SessionLocal() as session:
            await session.execute(text("SET search_path TO test_schema"))
            
            # Create a test user
            test_user = User(
                id=uuid4(),
                email="test@example.com",
                firstname="Test",
                lastname="User",
                hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                role=UserRole.CUSTOMER,
                verified=True,
                is_active=True,
                phone="+1234567890",
                country="US"
            )
            
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            
            print(f"✅ User created successfully: {test_user.email}")
            
            # Query the user back
            result = await session.execute(text("SELECT email FROM users WHERE email = :email"), {"email": "test@example.com"})
            user_email = result.scalar()
            print(f"✅ User queried successfully: {user_email}")
        
        # Cleanup
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS test_schema CASCADE"))
            print("✅ Test schema cleaned up")
        
        await engine.dispose()
        print("✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    success = await test_database_connection()
    if not success:
        sys.exit(1)
    print("🎉 Database is working correctly with your Neon PostgreSQL!")

if __name__ == "__main__":
    asyncio.run(main())