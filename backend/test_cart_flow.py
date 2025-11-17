"""
End-to-end test for cart functionality.
Tests: adding products, updating quantities, removing items, cart calculations, checkout.
"""
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"

class CartFlowTester:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.product_id: Optional[str] = None
        self.variant_id: Optional[str] = None
        self.variant_price: float = 0.0
        self.cart_item_id: Optional[str] = None
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
    
    def login(self, email: str = "admin@banwee.com", password: str = "adminpass"):
        """Login to get access token"""
        print("\n" + "="*60)
        print("STEP 1: Login")
        print("="*60)
        
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    self.access_token = data["data"].get("access_token")
                    self.user_id = data["data"].get("user", {}).get("id")
                    self.log_test("Login", True, f"User ID: {self.user_id}")
                    return True
                else:
                    self.log_test("Login", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Login", False, str(e))
            return False
    
    def get_product(self):
        """Get a product to add to cart"""
        print("\n" + "="*60)
        print("STEP 2: Get Product")
        print("="*60)
        
        try:
            response = requests.get(f"{BASE_URL}/products?page=1&per_page=50")
            
            if response.status_code == 200:
                data = response.json()
                products_data = data.get("data", {})
                if isinstance(products_data, dict):
                    products = products_data.get("data", [])
                else:
                    products = products_data
                
                if len(products) > 0:
                    # Find a product with variants and stock
                    for product in products:
                        product_id = product.get("id")
                        detail_response = requests.get(f"{BASE_URL}/products/{product_id}")
                        
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            if detail_data.get("success") and detail_data.get("data"):
                                product_detail = detail_data["data"]
                                variants = product_detail.get("variants", [])
                                
                                # Find variant with stock
                                for variant in variants:
                                    if variant.get("stock", 0) > 0:
                                        self.product_id = product_id
                                        self.variant_id = variant.get("id")
                                        self.variant_price = variant.get("sale_price") or variant.get("base_price", 0)
                                        self.log_test(
                                            "Get Product", 
                                            True, 
                                            f"Product: {product.get('name')}, Variant: {variant.get('name')}, Price: ${self.variant_price}"
                                        )
                                        return True
                    
                    self.log_test("Get Product", False, "No products with stock found")
                    return False
                else:
                    self.log_test("Get Product", False, "No products found")
                    return False
            else:
                self.log_test("Get Product", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Product", False, str(e))
            return False
    
    def clear_cart(self):
        """Clear cart before testing"""
        print("\n" + "="*60)
        print("STEP 3: Clear Cart")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/cart/clear",
                headers=headers
            )
            
            if response.status_code == 200:
                self.log_test("Clear Cart", True, "Cart cleared successfully")
                return True
            else:
                self.log_test("Clear Cart", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Clear Cart", False, str(e))
            return False
    
    def add_to_cart(self, quantity: int = 1):
        """Add product to cart"""
        print("\n" + "="*60)
        print(f"STEP 4: Add to Cart (Quantity: {quantity})")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/cart/add",
                json={
                    "variant_id": self.variant_id,
                    "quantity": quantity
                },
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    cart_data = data["data"]
                    items = cart_data.get("items", [])
                    
                    if len(items) > 0:
                        self.cart_item_id = items[0].get("id")
                        item_quantity = items[0].get("quantity")
                        
                        # Verify product name is included
                        variant = items[0].get("variant", {})
                        product_name = variant.get("product_name")
                        variant_name = variant.get("name")
                        
                        self.log_test(
                            "Add to Cart", 
                            True, 
                            f"Item ID: {self.cart_item_id}, Quantity: {item_quantity}, Product: {product_name}, Variant: {variant_name}"
                        )
                        
                        # Additional validation
                        if not product_name:
                            print("  ⚠️  Warning: product_name not included in response")
                        
                        return True
                    else:
                        self.log_test("Add to Cart", False, "No items in cart after adding")
                        return False
                else:
                    self.log_test("Add to Cart", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Add to Cart", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Add to Cart", False, str(e))
            return False
    
    def view_cart(self):
        """View cart contents"""
        print("\n" + "="*60)
        print("STEP 5: View Cart")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{BASE_URL}/cart/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    cart_data = data["data"]
                    items = cart_data.get("items", [])
                    subtotal = cart_data.get("subtotal", 0)
                    tax_amount = cart_data.get("tax_amount", 0)
                    shipping_amount = cart_data.get("shipping_amount", 0)
                    total_amount = cart_data.get("total_amount", 0)
                    
                    self.log_test(
                        "View Cart", 
                        True, 
                        f"Items: {len(items)}, Subtotal: ${subtotal:.2f}, Tax: ${tax_amount:.2f}, Shipping: ${shipping_amount:.2f}, Total: ${total_amount:.2f}"
                    )
                    
                    # Display item details
                    for item in items:
                        variant = item.get("variant", {})
                        print(f"  - {variant.get('product_name')} - {variant.get('name')}: ${item.get('price_per_unit'):.2f} x {item.get('quantity')} = ${item.get('total_price'):.2f}")
                    
                    return True
                else:
                    self.log_test("View Cart", False, "Invalid response structure")
                    return False
            else:
                self.log_test("View Cart", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("View Cart", False, str(e))
            return False
    
    def update_quantity(self, new_quantity: int = 3):
        """Update cart item quantity"""
        print("\n" + "="*60)
        print(f"STEP 6: Update Quantity to {new_quantity}")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.put(
                f"{BASE_URL}/cart/update/{self.cart_item_id}",
                json={"quantity": new_quantity},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    cart_data = data["data"]
                    items = cart_data.get("items", [])
                    
                    if len(items) > 0:
                        updated_item = items[0]
                        updated_quantity = updated_item.get("quantity")
                        
                        if updated_quantity == new_quantity:
                            self.log_test(
                                "Update Quantity", 
                                True, 
                                f"Quantity updated to {updated_quantity}"
                            )
                            return True
                        else:
                            self.log_test(
                                "Update Quantity", 
                                False, 
                                f"Expected {new_quantity}, got {updated_quantity}"
                            )
                            return False
                    else:
                        self.log_test("Update Quantity", False, "No items in cart")
                        return False
                else:
                    self.log_test("Update Quantity", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Update Quantity", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Update Quantity", False, str(e))
            return False
    
    def verify_calculations(self):
        """Verify cart calculations are correct"""
        print("\n" + "="*60)
        print("STEP 7: Verify Cart Calculations")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{BASE_URL}/cart/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    cart_data = data["data"]
                    items = cart_data.get("items", [])
                    subtotal = cart_data.get("subtotal", 0)
                    tax_amount = cart_data.get("tax_amount", 0)
                    shipping_amount = cart_data.get("shipping_amount", 0)
                    total_amount = cart_data.get("total_amount", 0)
                    
                    # Calculate expected values
                    expected_subtotal = sum(item.get("total_price", 0) for item in items)
                    expected_tax = expected_subtotal * 0.1  # 10% tax
                    expected_shipping = 0.0 if expected_subtotal >= 50 else 10.0
                    expected_total = expected_subtotal + expected_tax + expected_shipping
                    
                    # Verify calculations (with small tolerance for floating point)
                    subtotal_correct = abs(subtotal - expected_subtotal) < 0.01
                    tax_correct = abs(tax_amount - expected_tax) < 0.01
                    shipping_correct = abs(shipping_amount - expected_shipping) < 0.01
                    total_correct = abs(total_amount - expected_total) < 0.01
                    
                    all_correct = subtotal_correct and tax_correct and shipping_correct and total_correct
                    
                    if all_correct:
                        self.log_test(
                            "Verify Calculations", 
                            True, 
                            f"All calculations correct"
                        )
                    else:
                        errors = []
                        if not subtotal_correct:
                            errors.append(f"Subtotal: expected ${expected_subtotal:.2f}, got ${subtotal:.2f}")
                        if not tax_correct:
                            errors.append(f"Tax: expected ${expected_tax:.2f}, got ${tax_amount:.2f}")
                        if not shipping_correct:
                            errors.append(f"Shipping: expected ${expected_shipping:.2f}, got ${shipping_amount:.2f}")
                        if not total_correct:
                            errors.append(f"Total: expected ${expected_total:.2f}, got ${total_amount:.2f}")
                        
                        self.log_test(
                            "Verify Calculations", 
                            False, 
                            "; ".join(errors)
                        )
                    
                    return all_correct
                else:
                    self.log_test("Verify Calculations", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Verify Calculations", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Verify Calculations", False, str(e))
            return False
    
    def remove_from_cart(self):
        """Remove item from cart"""
        print("\n" + "="*60)
        print("STEP 8: Remove Item from Cart")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.delete(
                f"{BASE_URL}/cart/remove/{self.cart_item_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("Remove from Cart", True, "Item removed successfully")
                    return True
                else:
                    self.log_test("Remove from Cart", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Remove from Cart", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Remove from Cart", False, str(e))
            return False
    
    def verify_cart_empty(self):
        """Verify cart is empty after removal"""
        print("\n" + "="*60)
        print("STEP 9: Verify Cart Empty")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{BASE_URL}/cart/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    cart_data = data["data"]
                    items = cart_data.get("items", [])
                    
                    if len(items) == 0:
                        self.log_test("Verify Cart Empty", True, "Cart is empty")
                        return True
                    else:
                        self.log_test("Verify Cart Empty", False, f"Cart still has {len(items)} items")
                        return False
                else:
                    self.log_test("Verify Cart Empty", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Verify Cart Empty", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Verify Cart Empty", False, str(e))
            return False
    
    def test_checkout_summary(self):
        """Test checkout summary endpoint"""
        print("\n" + "="*60)
        print("STEP 10: Test Checkout Summary")
        print("="*60)
        
        try:
            # First add an item back to cart
            headers = {"Authorization": f"Bearer {self.access_token}"}
            add_response = requests.post(
                f"{BASE_URL}/cart/add",
                json={
                    "variant_id": self.variant_id,
                    "quantity": 2
                },
                headers=headers
            )
            
            if add_response.status_code != 200:
                self.log_test("Test Checkout Summary", False, "Failed to add item for checkout test")
                return False
            
            # Get checkout summary
            response = requests.get(
                f"{BASE_URL}/cart/checkout-summary",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    summary = data["data"]
                    
                    has_cart = "cart" in summary
                    has_payment_methods = "available_payment_methods" in summary
                    has_shipping_methods = "available_shipping_methods" in summary
                    has_tax_info = "tax_info" in summary
                    
                    all_present = has_cart and has_payment_methods and has_shipping_methods and has_tax_info
                    
                    if all_present:
                        cart = summary.get("cart", {})
                        items = cart.get("items", [])
                        self.log_test(
                            "Test Checkout Summary", 
                            True, 
                            f"Summary includes cart ({len(items)} items), payment methods, shipping methods, and tax info"
                        )
                        return True
                    else:
                        missing = []
                        if not has_cart:
                            missing.append("cart")
                        if not has_payment_methods:
                            missing.append("payment_methods")
                        if not has_shipping_methods:
                            missing.append("shipping_methods")
                        if not has_tax_info:
                            missing.append("tax_info")
                        
                        self.log_test(
                            "Test Checkout Summary", 
                            False, 
                            f"Missing: {', '.join(missing)}"
                        )
                        return False
                else:
                    self.log_test("Test Checkout Summary", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Test Checkout Summary", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Test Checkout Summary", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all cart flow tests"""
        print("\n" + "="*60)
        print("CART END-TO-END FLOW TEST")
        print("="*60)
        print("\nPrerequisites:")
        print("- Backend server must be running on http://localhost:8000")
        print("- Database must have products with stock > 0")
        print("- Admin user (admin@banwee.com) must exist")
        print("="*60)
        
        # Run tests in sequence
        if not self.login():
            print("\n❌ Cannot proceed without login")
            print("   Make sure the backend server is running and admin user exists")
            return False
        
        if not self.get_product():
            print("\n❌ Cannot proceed without product")
            print("   Make sure the database has products with stock > 0")
            print("   You can add products through the admin interface or API")
            return False
        
        if not self.clear_cart():
            print("\n⚠️  Cart clearing has issues")
        
        if not self.add_to_cart(quantity=2):
            print("\n❌ Cannot proceed without adding to cart")
            return False
        
        if not self.view_cart():
            print("\n⚠️  Cart viewing has issues")
        
        if not self.update_quantity(new_quantity=3):
            print("\n⚠️  Quantity update has issues")
        
        if not self.verify_calculations():
            print("\n⚠️  Cart calculations have issues")
        
        if not self.remove_from_cart():
            print("\n⚠️  Removing items has issues")
        
        if not self.verify_cart_empty():
            print("\n⚠️  Cart verification has issues")
        
        if not self.test_checkout_summary():
            print("\n⚠️  Checkout summary has issues")
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed!")
            return True
        else:
            print("\n⚠️  Some tests failed. Review the output above.")
            return False

if __name__ == "__main__":
    tester = CartFlowTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
