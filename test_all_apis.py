#!/usr/bin/env python3
"""
Comprehensive API Testing Script
Tests all API endpoints to ensure they are working correctly
"""

import requests
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_VERSION = "v1"
API_BASE = f"{BASE_URL}/{API_VERSION}"

# Test credentials
TEST_USER = {
    "email": "user3@example.com",
    "password": "P@ss0003",
    "first_name": "Test",
    "last_name": "User"
}

TEST_ADMIN = {
    "email": "admin@banwee.com",
    "password": "adminpass"
}

# Global variables for test data
auth_token = None
admin_token = None
test_user_id = None
test_product_id = None
test_variant_id = None
test_order_id = None
test_cart_id = None
test_address_id = None

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": []
}


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_test(name: str, status: str, message: str = ""):
    """Print test result"""
    if status == "PASS":
        color = Colors.GREEN
        test_results["passed"] += 1
    elif status == "FAIL":
        color = Colors.RED
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {message}")
    else:  # SKIP
        color = Colors.YELLOW
        test_results["skipped"] += 1
    
    status_text = f"[{status}]"
    print(f"{color}{status_text:8}{Colors.RESET} {name}")
    if message:
        print(f"         {message}")


def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None
) -> tuple[bool, Any, str]:
    """Make HTTP request and return success status, response data, and message"""
    url = f"{API_BASE}{endpoint}" if endpoint.startswith("/") else f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return False, None, f"Unsupported method: {method}"
        
        # Check if response is successful
        if response.status_code in [200, 201]:
            try:
                return True, response.json(), f"Status: {response.status_code}"
            except:
                return True, response.text, f"Status: {response.status_code}"
        else:
            try:
                error_data = response.json()
                return False, error_data, f"Status: {response.status_code} - {error_data.get('message', 'Unknown error')}"
            except:
                return False, None, f"Status: {response.status_code} - {response.text[:100]}"
    
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error - Is the server running?"
    except requests.exceptions.Timeout:
        return False, None, "Request timeout"
    except Exception as e:
        return False, None, f"Error: {str(e)}"


def test_health_endpoints():
    """Test health check endpoints"""
    print_header("HEALTH CHECK ENDPOINTS")
    
    # Test root endpoint
    success, data, msg = make_request("GET", "/")
    print_test("GET /", "PASS" if success else "FAIL", msg)
    
    # Test liveness
    success, data, msg = make_request("GET", "/health/live")
    print_test("GET /v1/health/live", "PASS" if success else "FAIL", msg)
    
    # Test readiness
    success, data, msg = make_request("GET", "/health/ready")
    print_test("GET /v1/health/ready", "PASS" if success else "FAIL", msg)
    
    # Test detailed health
    success, data, msg = make_request("GET", "/health/detailed")
    print_test("GET /v1/health/detailed", "PASS" if success else "FAIL", msg)


def test_auth_endpoints():
    """Test authentication endpoints"""
    global auth_token, test_user_id
    
    print_header("AUTHENTICATION ENDPOINTS")
    
    # Test user login (skip registration since user exists)
    login_data = {"email": TEST_USER["email"], "password": TEST_USER["password"]}
    success, data, msg = make_request("POST", "/auth/login", login_data)
    if success and data.get("data"):
        auth_token = data["data"].get("access_token")
        if data["data"].get("user"):
            test_user_id = data["data"]["user"].get("id")
    print_test("POST /v1/auth/login", "PASS" if success else "FAIL", msg)
    
    if not auth_token:
        print_test("Authentication", "FAIL", "Could not obtain auth token")
        return
    
    # Test get profile
    success, data, msg = make_request("GET", "/auth/profile", token=auth_token)
    print_test("GET /v1/auth/profile", "PASS" if success else "FAIL", msg)
    
    # Test update profile
    update_data = {"first_name": "Updated"}
    success, data, msg = make_request("PUT", "/auth/profile", update_data, token=auth_token)
    print_test("PUT /v1/auth/profile", "PASS" if success else "FAIL", msg)


def test_product_endpoints():
    """Test product endpoints"""
    global test_product_id, test_variant_id
    
    print_header("PRODUCT ENDPOINTS")
    
    # Test get all products
    success, data, msg = make_request("GET", "/products", params={"page": 1, "limit": 10})
    if success and data.get("data", {}).get("data"):
        products = data["data"]["data"]
        if products:
            test_product_id = products[0].get("id")
    print_test("GET /v1/products", "PASS" if success else "FAIL", msg)
    
    # Test get categories
    success, data, msg = make_request("GET", "/products/categories")
    print_test("GET /v1/products/categories", "PASS" if success else "FAIL", msg)
    
    # Test get home page data
    success, data, msg = make_request("GET", "/products/home")
    print_test("GET /v1/products/home", "PASS" if success else "FAIL", msg)
    
    if test_product_id:
        # Test get product by ID
        success, data, msg = make_request("GET", f"/products/{test_product_id}")
        print_test(f"GET /v1/products/{test_product_id}", "PASS" if success else "FAIL", msg)
        
        # Test get product variants
        success, data, msg = make_request("GET", f"/products/{test_product_id}/variants")
        if success and data.get("data"):
            variants = data["data"]
            if variants:
                test_variant_id = variants[0].get("id")
        print_test(f"GET /v1/products/{test_product_id}/variants", "PASS" if success else "FAIL", msg)
        
        # Test get recommendations
        success, data, msg = make_request("GET", f"/products/{test_product_id}/recommendations")
        print_test(f"GET /v1/products/{test_product_id}/recommendations", "PASS" if success else "FAIL", msg)


def test_cart_endpoints():
    """Test cart endpoints"""
    global test_cart_id
    
    print_header("CART ENDPOINTS")
    
    if not auth_token:
        print_test("Cart tests", "SKIP", "No auth token available")
        return
    
    # Test get cart
    success, data, msg = make_request("GET", "/cart", token=auth_token)
    if success and data.get("data"):
        test_cart_id = data["data"].get("id")
    print_test("GET /v1/cart", "PASS" if success else "FAIL", msg)
    
    # Test add to cart
    if test_variant_id:
        cart_item = {"variant_id": test_variant_id, "quantity": 1}
        success, data, msg = make_request("POST", "/cart/add", cart_item, token=auth_token)
        print_test("POST /v1/cart/add", "PASS" if success else "FAIL", msg)
    else:
        print_test("POST /v1/cart/add", "SKIP", "No variant ID available")
    
    # Test get cart count
    success, data, msg = make_request("GET", "/cart/count", token=auth_token)
    print_test("GET /v1/cart/count", "PASS" if success else "FAIL", msg)
    
    # Test validate cart
    success, data, msg = make_request("POST", "/cart/validate", token=auth_token)
    print_test("POST /v1/cart/validate", "PASS" if success else "FAIL", msg)
    
    # Test get checkout summary
    success, data, msg = make_request("GET", "/cart/checkout-summary", token=auth_token)
    print_test("GET /v1/cart/checkout-summary", "PASS" if success else "FAIL", msg)


def test_user_endpoints():
    """Test user management endpoints"""
    global test_address_id
    
    print_header("USER MANAGEMENT ENDPOINTS")
    
    if not auth_token:
        print_test("User tests", "SKIP", "No auth token available")
        return
    
    # Test get addresses
    success, data, msg = make_request("GET", "/auth/addresses", token=auth_token)
    print_test("GET /v1/auth/addresses", "PASS" if success else "FAIL", msg)
    
    # Test create address
    address_data = {
        "street": "123 Test St",
        "city": "Test City",
        "state": "TS",
        "country": "Test Country",
        "post_code": "12345"
    }
    success, data, msg = make_request("POST", "/auth/addresses", address_data, token=auth_token)
    if success and data.get("data"):
        test_address_id = data["data"].get("id")
    print_test("POST /v1/auth/addresses", "PASS" if success else "FAIL", msg)


def test_order_endpoints():
    """Test order endpoints"""
    global test_order_id
    
    print_header("ORDER ENDPOINTS")
    
    if not auth_token:
        print_test("Order tests", "SKIP", "No auth token available")
        return
    
    # Test get orders
    success, data, msg = make_request("GET", "/orders", token=auth_token, params={"page": 1, "limit": 10})
    if success and data.get("data", {}).get("orders"):
        orders = data["data"]["orders"]
        if orders:
            test_order_id = orders[0].get("id")
    print_test("GET /v1/orders", "PASS" if success else "FAIL", msg)
    
    if test_order_id:
        # Test get order by ID
        success, data, msg = make_request("GET", f"/orders/{test_order_id}", token=auth_token)
        print_test(f"GET /v1/orders/{test_order_id}", "PASS" if success else "FAIL", msg)
        
        # Test get order tracking
        success, data, msg = make_request("GET", f"/orders/{test_order_id}/tracking", token=auth_token)
        print_test(f"GET /v1/orders/{test_order_id}/tracking", "PASS" if success else "FAIL", msg)


def test_notification_endpoints():
    """Test notification endpoints"""
    print_header("NOTIFICATION ENDPOINTS")
    
    if not auth_token:
        print_test("Notification tests", "SKIP", "No auth token available")
        return
    
    # Test get notifications
    success, data, msg = make_request("GET", "/notifications", token=auth_token, params={"page": 1, "limit": 10})
    print_test("GET /v1/notifications", "PASS" if success else "FAIL", msg)


def test_payment_endpoints():
    """Test payment endpoints"""
    print_header("PAYMENT ENDPOINTS")
    
    if not auth_token:
        print_test("Payment tests", "SKIP", "No auth token available")
        return
    
    # Test get payment methods
    success, data, msg = make_request("GET", "/users/me/payment-methods", token=auth_token)
    print_test("GET /v1/users/me/payment-methods", "PASS" if success else "FAIL", msg)


def test_review_endpoints():
    """Test review endpoints"""
    print_header("REVIEW ENDPOINTS")
    
    if test_product_id:
        # Test get product reviews
        success, data, msg = make_request("GET", f"/reviews/product/{test_product_id}", params={"page": 1, "limit": 10})
        print_test(f"GET /v1/reviews/product/{test_product_id}", "PASS" if success else "FAIL", msg)
    else:
        print_test("Review tests", "SKIP", "No product ID available")


def test_wishlist_endpoints():
    """Test wishlist endpoints"""
    print_header("WISHLIST ENDPOINTS")
    
    if not auth_token:
        print_test("Wishlist tests", "SKIP", "No auth token available")
        return
    
    # Test get wishlist
    success, data, msg = make_request("GET", "/wishlist", token=auth_token)
    print_test("GET /v1/wishlist", "PASS" if success else "FAIL", msg)


def test_search_endpoints():
    """Test search endpoints"""
    print_header("SEARCH ENDPOINTS")
    
    # Test autocomplete search
    success, data, msg = make_request("GET", "/search/autocomplete", params={"q": "test", "type": "product", "limit": 10})
    print_test("GET /v1/search/autocomplete", "PASS" if success else "FAIL", msg)


def test_subscription_endpoints():
    """Test subscription endpoints"""
    print_header("SUBSCRIPTION ENDPOINTS")
    
    if not auth_token:
        print_test("Subscription tests", "SKIP", "No auth token available")
        return
    
    # Test get subscriptions
    success, data, msg = make_request("GET", "/subscriptions", token=auth_token, params={"page": 1, "limit": 10})
    print_test("GET /v1/subscriptions", "PASS" if success else "FAIL", msg)


def test_loyalty_endpoints():
    """Test loyalty endpoints"""
    print_header("LOYALTY ENDPOINTS")
    
    if not auth_token:
        print_test("Loyalty tests", "SKIP", "No auth token available")
        return
    
    # Test get loyalty points
    success, data, msg = make_request("GET", "/loyalty/points", token=auth_token)
    print_test("GET /v1/loyalty/points", "PASS" if success else "FAIL", msg)


def test_inventory_endpoints():
    """Test inventory endpoints"""
    print_header("INVENTORY ENDPOINTS")
    
    if not auth_token:
        print_test("Inventory tests", "SKIP", "No auth token available")
        return
    
    # Test get inventory
    success, data, msg = make_request("GET", "/inventory", token=auth_token, params={"page": 1, "limit": 10})
    print_test("GET /v1/inventory", "PASS" if success else "FAIL", msg)


def test_analytics_endpoints():
    """Test analytics endpoints"""
    print_header("ANALYTICS ENDPOINTS")
    
    if not auth_token:
        print_test("Analytics tests", "SKIP", "No auth token available")
        return
    
    # Test get dashboard analytics
    success, data, msg = make_request("GET", "/analytics/dashboard", token=auth_token)
    print_test("GET /v1/analytics/dashboard", "PASS" if success else "FAIL", msg)


def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = test_results["passed"] + test_results["failed"] + test_results["skipped"]
    
    print(f"{Colors.GREEN}Passed:  {test_results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}Failed:  {test_results['failed']}{Colors.RESET}")
    print(f"{Colors.YELLOW}Skipped: {test_results['skipped']}{Colors.RESET}")
    print(f"{Colors.BOLD}Total:   {total}{Colors.RESET}")
    
    if test_results["failed"] > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.RESET}")
        for error in test_results["errors"]:
            print(f"  {Colors.RED}• {error}{Colors.RESET}")
    
    success_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.RESET}")
    
    return test_results["failed"] == 0


def main():
    """Main test runner"""
    print(f"\n{Colors.BOLD}API Testing Suite{Colors.RESET}")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all test suites
    test_health_endpoints()
    test_auth_endpoints()
    test_product_endpoints()
    test_cart_endpoints()
    test_user_endpoints()
    test_order_endpoints()
    test_notification_endpoints()
    test_payment_endpoints()
    test_review_endpoints()
    test_wishlist_endpoints()
    test_search_endpoints()
    test_subscription_endpoints()
    test_loyalty_endpoints()
    test_inventory_endpoints()
    test_analytics_endpoints()
    
    # Print summary
    success = print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
