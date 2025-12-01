import asyncio
from sqlalchemy import select, text
from core.database import AsyncSessionDB
from models.product import Product, ProductVariant

async def test_uuid_storage():
    async with AsyncSessionDB() as session:
        # Get raw data from database
        result = await session.execute(text("""
            SELECT id, name FROM products WHERE featured = TRUE LIMIT 2
        """))
        print("Products (raw):")
        for row in result:
            print(f"  ID: {row[0]} | Name: {row[1]}")
        
        result = await session.execute(text("""
            SELECT id, product_id, name FROM product_variants LIMIT 5
        """))
        print("\nVariants (raw):")
        for row in result:
            print(f"  ID: {row[0]} | Product ID: {row[1]} | Name: {row[2]}")
        
        # Try a raw JOIN
        result = await session.execute(text("""
            SELECT p.id, p.name, v.id, v.name
            FROM products p
            JOIN product_variants v ON p.id = v.product_id
            WHERE p.featured = TRUE
            LIMIT 5
        """))
        print("\nJOIN results (raw SQL):")
        rows = result.all()
        print(f"Found {len(rows)} rows")
        for row in rows:
            print(f"  Product: {row[1]} | Variant: {row[3]}")

if __name__ == "__main__":
    asyncio.run(test_uuid_storage())
