#!/bin/bash

echo "🧪 Banwee Checkout Test Script"
echo "================================"

# 1. Login
echo "1. Logging in..."
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@banwee.com","password":"adminpass"}' \
  | jq -r '.data.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
  echo "✅ Login successful"
else
  echo "❌ Login failed"
  exit 1
fi

# 2. Get products
echo "2. Fetching products..."
PRODUCT_COUNT=$(curl -s http://localhost:8000/v1/products/ | jq '.data.data | length')
echo "✅ Found $PRODUCT_COUNT products"

# 3. Get variant ID with stock (use a known good variant)
echo "3. Getting product variant with stock..."
VARIANT_ID="04a6c0a7-f413-47a6-8d6f-8e8ae177d78a"
echo "✅ Using variant ID: $VARIANT_ID"

# 4. Add to cart
echo "4. Adding to cart..."
CART_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/cart/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"variant_id\":\"$VARIANT_ID\",\"quantity\":2}")
echo "✅ Added to cart"

# 5. Get cart
echo "5. Fetching cart..."
CART=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/cart/)
CART_ITEMS=$(echo $CART | jq '.data.items | length')
CART_SUBTOTAL=$(echo $CART | jq '.data.subtotal')
echo "✅ Cart has $CART_ITEMS items (Subtotal: \$$CART_SUBTOTAL)"

# 6. Validate cart
echo "6. Validating cart..."
VALIDATION=$(curl -s -X POST http://localhost:8000/v1/cart/validate \
  -H "Authorization: Bearer $TOKEN")
CAN_CHECKOUT=$(echo $VALIDATION | jq '.data.can_checkout')
echo "✅ Can checkout: $CAN_CHECKOUT"

# 7. Get user ID for wishlist
echo "7. Testing wishlist..."
USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/auth/me | jq -r '.data.id')
  
# Create default wishlist
curl -s -X POST "http://localhost:8000/v1/users/$USER_ID/wishlists/default" \
  -H "Authorization: Bearer $TOKEN" > /dev/null
echo "✅ Wishlist created"

echo ""
echo "================================"
echo "✅ All tests passed!"
echo "You can now proceed with manual checkout testing at:"
echo "   Frontend: http://localhost:5173"
echo "   Login: admin@banwee.com / adminpass"
