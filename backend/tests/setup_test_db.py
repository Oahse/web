#!/usr/bin/env python3
"""
Script to set up PostgreSQL test schema for running tests
"""
import asyncio
import asyncpg
import sys

async def create_test_schema():
    """Create test schema if it doesn't exist"""
    try:
        # Connect to Neon PostgreSQL database
        conn = await asyncpg.connect(
            "postgresql://neondb_owner:npg_qI9D0igTcRXw@ep-plain-morning-ah8l56gm-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        )
        
        # Check if test schema exists
        test_schema_name = 'test_schema'
        result = await conn.fetchval(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = $1", test_schema_name
        )
        
        if not result:
            # Create test schema
            await conn.execute(f'CREATE SCHEMA "{test_schema_name}"')
            print(f"✅ Created test schema: {test_schema_name}")
        else:
            print(f"✅ Test schema already exists: {test_schema_name}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating test schema: {e}")
        return False

async def drop_test_schema():
    """Drop test schema"""
    try:
        # Connect to Neon PostgreSQL database
        conn = await asyncpg.connect(
            "postgresql://neondb_owner:npg_qI9D0igTcRXw@ep-plain-morning-ah8l56gm-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        )
        
        test_schema_name = 'test_schema'
        
        # Drop test schema
        await conn.execute(f'DROP SCHEMA IF EXISTS "{test_schema_name}" CASCADE')
        print(f"✅ Dropped test schema: {test_schema_name}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error dropping test schema: {e}")
        return False

async def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == 'drop':
        success = await drop_test_schema()
    else:
        success = await create_test_schema()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())