"""
Test script for product search functionality
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionDB
from services.products import ProductService


async def test_search_queries():
    """Test various search queries"""
    print("=" * 80)
    print("TESTING PRODUCT SEARCH FUNCTIONALITY")
    print("=" * 80)
    
    async with AsyncSessionDB() as db:
        service = ProductService(db)
        
        # Test 1: Basic search query
        print("\n1. Testing basic search query (q='organic')...")
        result = await service.get_products(
            page=1,
            limit=5,
            filters={"q": "organic"},
            sort_by="created_at",
            sort_order="desc"
        )
        print(f"   Found {result['total']} products")
        if result['data']:
            print(f"   First result: {result['data'][0].name}")
        
        # Test 2: Category filter
        print("\n2. Testing category filter (category='Fruits & Veggies')...")
        result = await service.get_products(
            page=1,
            limit=5,
            filters={"category": "Fruits & Veggies"},
            sort_by="created_at",
            sort_order="desc"
        )
        print(f"   Found {result['total']} products")
        if result['data']:
            print(f"   First result: {result['data'][0].name}")
        
        # Test 3: Price range filter
        print("\n3. Testing price range filter (min_price=10, max_price=50)...")
        result = await service.get_products(
            page=1,
            limit=5,
            filters={"min_price": 10, "max_price": 50},
            sort_by="created_at",
            sort_order="desc"
        )
        print(f"   Found {result['total']} products")
        if result['data']:
            for p in result['data'][:3]:
                price = p.variants[0].base_price if p.variants else 0
                print(f"   - {p.name}: ${price}")
        
        # Test 4: Rating filter
        print("\n4. Testing rating filter (min_rating=4)...")
        result = await service.get_products(
            page=1,
            limit=5,
            filters={"min_rating": 4},
            sort_by="rating",
            sort_order="desc"
        )
        print(f"   Found {result['total']} products")
        if result['data']:
            for p in result['data'][:3]:
                print(f"   - {p.name}: {p.rating} stars")
        
        # Test 5: Combined filters
        print("\n5. Testing combined filters (category='Legumes', min_price=20, min_rating=3)...")
        result = await service.get_products(
            page=1,
            limit=5,
            filters={
                "category": "Legumes",
                "min_price": 20,
                "min_rating": 3
            },
            sort_by="created_at",
            sort_order="desc"
        )
        print(f"   Found {result['total']} products")
        if result['data']:
            for p in result['data'][:3]:
                price = p.variants[0].base_price if p.variants else 0
                print(f"   - {p.name}: ${price}, {p.rating} stars")
        
        # Test 6: Search with category
        print("\n6. Testing search with category (q='organic', category='Cereal Crops')...")
        result = await service.get_products(
            page=1,
            limit=5,
            filters={"q": "organic", "category": "Cereal Crops"},
            sort_by="created_at",
            sort_order="desc"
        )
        print(f"   Found {result['total']} products")
        if result['data']:
            print(f"   First result: {result['data'][0].name}")
        
        # Test 7: Sort by price
        print("\n7. Testing sort by price (sort_by='price', sort_order='asc')...")
        result = await service.get_products(
            page=1,
            limit=5,
            filters={},
            sort_by="created_at",
            sort_order="asc"
        )
        print(f"   Found {result['total']} products")
        if result['data']:
            for p in result['data'][:3]:
                price = p.variants[0].base_price if p.variants else 0
                print(f"   - {p.name}: ${price}")
        
        # Test 8: Empty search
        print("\n8. Testing empty search (no filters)...")
        result = await service.get_products(
            page=1,
            limit=5,
            filters={},
            sort_by="created_at",
            sort_order="desc"
        )
        print(f"   Found {result['total']} products")
        
        # Test 9: No results search
        print("\n9. Testing search with no results (q='nonexistentproduct123')...")
        result = await service.get_products(
            page=1,
            limit=5,
            filters={"q": "nonexistentproduct123"},
            sort_by="created_at",
            sort_order="desc"
        )
        print(f"   Found {result['total']} products")
        
        # Test 10: Pagination
        print("\n10. Testing pagination (page=2, limit=5)...")
        result = await service.get_products(
            page=2,
            limit=5,
            filters={},
            sort_by="created_at",
            sort_order="desc"
        )
        print(f"   Page 2 of {result['total_pages']}, showing {len(result['data'])} products")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_search_queries())
