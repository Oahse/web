import asyncio
import json
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.database import AsyncSessionDB
from models.product import Product, ProductVariant, Category
from services.products import ProductService

async def test_home_endpoint():
    async with AsyncSessionDB() as session:
        product_service = ProductService(session)
        
        print("Testing featured products...")
        featured = await product_service.get_featured_products(limit=4)
        print(f"Featured products returned: {len(featured)}")
        for p in featured:
            print(f"  - {p.name}")
            print(f"    Variants: {len(p.variants)}")
            if p.variants:
                for v in p.variants[:2]:
                    print(f"      * {v.name}: ${v.current_price}")
        
        print("\n" + "="*50)
        print("Testing direct query...")
        query = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.supplier),
                selectinload(Product.variants).selectinload(ProductVariant.images)
            )
            .where(Product.featured == True)
            .limit(2)
        )
        result = await session.execute(query)
        products = result.scalars().unique().all()
        
        print(f"Direct query returned: {len(products)} products")
        for p in products:
            print(f"  - {p.name} (ID: {p.id})")
            print(f"    Variants loaded: {len(p.variants)}")
            for v in p.variants[:2]:
                print(f"      * {v.name} (SKU: {v.sku}): ${v.base_price}")

if __name__ == "__main__":
    asyncio.run(test_home_endpoint())
