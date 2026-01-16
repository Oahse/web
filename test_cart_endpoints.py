#!/usr/bin/env python3
"""
Test script for cart endpoints
Demonstrates the proper use of cart_item_id vs variant_id
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/v1"
ACCESS_TOKEN = "your_access_token_here"  # Replace with actual token

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print()

def test_cart_workflow():
    """Test complete cart workflow with proper ID usage"""
    
    # Step 1: Get current cart
    print("\n🛒 Step 1: Get Current Cart")
    response = requests.get(f"{BASE_URL}/cart", headers=headers)
    print_response("GET /cart", response)
    
    if response.status_code == 200:
        cart = response.json().get("data", {})
        items = cart.get("items", [])
        
        if items:
            # Get the first item's IDs
            first_item = items[0]
            cart_item_id = first_item.get("id")
            variant_id = first_item.get("variant_id")
            product_id = first_item.get("product_id")
            
            print(f"\n📋 First Item IDs:")
            print(f"   cart_item_id: {cart_item_id}")
            print(f"   variant_id:   {variant_id}")
            print(f"   product_id:   {product_id}")
            
            # Step 2: Update quantity using cart_item_id
            print(f"\n✏️  Step 2: Update Quantity (using cart_item_id)")
            response = requests.put(
                f"{BASE_URL}/cart/items/{cart_item_id}?country=CA&province=ON",
                headers=headers,
                json={"quantity": 3}
            )
            print_response(f"PUT /cart/items/{cart_item_id}", response)
            
            # Step 3: Get cart again to see changes
            print("\n🔄 Step 3: Get Updated Cart")
            response = requests.get(f"{BASE_URL}/cart?country=CA&province=ON", headers=headers)
            print_response("GET /cart", response)
            
            # Step 4: Remove item using cart_item_id
            print(f"\n🗑️  Step 4: Remove Item (using cart_item_id)")
            response = requests.delete(
                f"{BASE_URL}/cart/items/{cart_item_id}",
                headers=headers
            )
            print_response(f"DELETE /cart/items/{cart_item_id}", response)
            
        else:
            print("\n⚠️  Cart is empty. Add some items first!")
            print("\nTo add an item, use variant_id:")
            print(f"POST {BASE_URL}/cart/add")
            print('{"variant_id": "your-variant-id", "quantity": 1}')
    
    # Step 5: Clear cart
    print("\n🧹 Step 5: Clear Cart")
    response = requests.post(f"{BASE_URL}/cart/clear", headers=headers)
    print_response("POST /cart/clear", response)

def test_add_to_cart():
    """Test adding item to cart using variant_id"""
    
    # Example variant_id - replace with actual one from your database
    variant_id = "efa8bff3-10f4-4ff2-bf27-b55cd22bb0c8"
    
    print("\n➕ Adding Item to Cart (using variant_id)")
    response = requests.post(
        f"{BASE_URL}/cart/add",
        headers=headers,
        json={
            "variant_id": variant_id,
            "quantity": 1
        }
    )
    print_response("POST /cart/add", response)
    
    if response.status_code == 200:
        cart = response.json().get("data", {})
        items = cart.get("items", [])
        if items:
            item = items[0]
            print(f"\n✅ Item added successfully!")
            print(f"   cart_item_id: {item.get('id')}")
            print(f"   variant_id:   {item.get('variant_id')}")
            print(f"\n💡 Use cart_item_id ({item.get('id')}) for updates/deletes")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Cart API Test - ID Usage Demonstration            ║
╚══════════════════════════════════════════════════════════════╝

This script demonstrates the proper use of IDs in cart operations:

  📦 variant_id   → Used to ADD items to cart
  🎫 cart_item_id → Used to UPDATE/DELETE items in cart
  📋 product_id   → Reference to product details

""")
    
    choice = input("Choose test:\n1. Full workflow (requires items in cart)\n2. Add item to cart\n\nEnter choice (1 or 2): ")
    
    if choice == "1":
        test_cart_workflow()
    elif choice == "2":
        test_add_to_cart()
    else:
        print("Invalid choice")
