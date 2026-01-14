#!/usr/bin/env python3
"""
Corrected API Testing Script
Tests all API endpoints with correct paths and parameters
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
    "password": "P@ss0003"
}

TEST_ADMIN = {
    "email": "admin@banwee.com",
    "password": "adminpass"
}

# Global variables
auth_token = None
admin_token = None
test_user_id = None
test_product_id = None
test_variant_id = None
test_order_id = None

test_results = {"passed": 0, "failed": 0, "skipped": 0, "errors": []}


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_test(name: str, status: str, message: str = ""):
    if status == "PASS":
        color = Colors.GREEN
        test_results["passed"] += 1
    elif status == "FAIL":
        color = Colors.RED
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {message}")
    else:
        color = Colors.YELLOW
        test_results["skipped"] += 1
    
    print(f"{color}[{status:4}]{Colors.RESET} {name}")
    if message and status != "PASS":
        print(f"       {message}")


def make_request(method: str, endpoint: str, data: Optional[Dict] = None, 
                token: Optional[str] = None, params: Optional[Dict] = None) -> tuple:
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
        
        if response.status_code in [200, 201]:
            try:
                return True, response.json(), f"Status: {response.status_code}"
            except:
                return True, response.text, f"Status: {response.status_code}"
        else:
            try:
                error_data = response.json()
                return False, error_data, f"Status: {response.status_code}"
            except:
                return False, None, f"Status: {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error"
    except requests.exceptions.Timeout:
        return False, None, "Timeout"
    except Exception as e:
        return False, None, f"Error: {str(e)}"


def test_authentication():
    global auth_token, test_user_id, admin_token
    
    print_header("AUTHENTICATION")
    
    # User login
    success, data, msg = make_request("POST", "/auth/login", TEST_USER)
    if success and data.get("data"):
        auth_token = data["data"].get("access_token")
        if data["data"].get("user"):
            test_user_id = data["data"]["user"].get("id")
    print_test("POST /v1/auth/login (User)", "PASS" if success else "FAIL", msg)
    
    # Admin login
    success, data, msg = make_request("POST", "/auth/login", TEST_ADMIN)
    if success and data.get("data"):
        admin_token = data["data"].get("access_token")
    print_test("POST /v1/auth/login (Admin)", "PASS" if success else "FAIL", msg)
    
    if not auth_token:
        print_test("Authentication Setup", "FAIL", "Could not obtain user token")
        return False
    
    # Get profile
    success, data, msg = make_request("GET", "/auth/profile", token=auth_token)
    print_test("GET /v1/auth/profile", "PASS" if success else "FAIL", msg)
    
    return True


def test_products():
    global test_product_id, test_variant_id
    
    print_header("PRODUCTS")
    
    # Get all products
    success, data, msg = make_request("GET", "/products", params={"page": 1, "limit": 10})
    if success and data.get("data", {}).get("data"):
        products = data["data"]["data"]
        if products:
            test_product_id = products[0].get("id")
    print_test("GET /v1/products", "PASS" if success else "FAIL", msg)
    
    # Get categories
    success, data, msg = make_request("GET", "/products/categories")
    print_test("GET /v1/products/categories", "PASS" if success else "FAIL", msg)
    
    # Get home data
    success, data, msg = make_request("GET", "/products/home")
    print_test("GET /v1/products/home", "PASS" if success else "FAIL", msg)
    
    if test_product_id:
        # Get product by ID
        success, data, msg = make_request("GET", f"/products/{test_product_id}")
        print_test(f"GET /v1/products/{{id}}", "PASS" if success else "FAIL", msg)
        
        # Get variants
        success, data, msg = make_request("GET", f"/products/{test_product_id}/variants")
        if success and data.get("data"):
            variants = data["data"]
            if variants:
                test_variant_id = variants[0].get("id")
        print_test(f"GET /v1/products/{{id}}/variants", "PASS" if success else "FAIL", msg)


def test_cart():
    print_header("CART")
    
    if not auth_token:
        print_test("Cart tests", "SKIP", "No auth token")
        return
    
    # Get cart
    success, data, msg = make_request("GET", "/cart", token=auth_token)
    print_test("GET /v1/cart", "PASS" if success else "FAIL", msg)
    
    # Add to cart
    if test_variant_id:
        cart_item = {"variant_id": test_variant_id, "quantity": 1}
        success, data, msg = make_request("POST", "/cart/add", cart_item, token=auth_token)
        print_test("POST /v1/cart/add", "PASS" if success else "FAIL", msg)
    
    # Get cart count
    success, data, msg = make_request("GET", "/cart/count", token=auth_token)
    print_test("GET /v1/cart/count", "PASS" if success else "FAIL", msg)
    
    # Validate cart
    success, data, msg = make_request("POST", "/cart/validate", token=auth_token)
    print_test("POST /v1/cart/validate", "PASS" if success else "FAIL", msg)


def test_orders():
    global test_order_id
    
    print_header("ORDERS")
    
    if not auth_token:
        print_test("Order tests", "SKIP", "No auth token")
        return
    
    # Get orders
    success, data, msg = make_request("GET", "/orders", token=auth_token)
    if success and data.get("data", {}).get("orders"):
        orders = data["data"]["orders"]
        if orders:
            test_order_id = orders[0].get("id")
    print_test("GET /v1/orders", "PASS" if success else "FAIL", msg)
    
    if test_order_id:
        # Get order by ID
        success, data, msg = make_request("GET", f"/orders/{test_order_id}", token=auth_token)
        print_test("GET /v1/orders/{id}", "PASS" if success else "FAIL", msg)


def test_user_management():
    print_header("USER MANAGEMENT")
    
    if not auth_token:
        print_test("User tests", "SKIP", "No auth token")
        return
    
    # Get addresses
    success, data, msg = make_request("GET", "/auth/addresses", token=auth_token)
    print_test("GET /v1/auth/addresses", "PASS" if success else "FAIL", msg)
    
    # Get payment methods (corrected path)
    success, data, msg = make_request("GET", "/payments/methods", token=auth_token)
    print_test("GET /v1/payments/methods", "PASS" if success else "FAIL", msg)


def test_wishlist():
    print_header("WISHLIST")
    
    if not auth_token:
        print_test("Wishlist tests", "SKIP", "No auth token")
        return
    
    # Get wishlists (corrected path - using me endpoint)
    success, data, msg = make_request("GET", "/users/me/wishlists", token=auth_token)
    print_test("GET /v1/users/me/wishlists", "PASS" if success else "FAIL", msg)


def test_loyalty():
    print_header("LOYALTY")
    
    if not auth_token:
        print_test("Loyalty tests", "SKIP", "No auth token")
        return
    
    # Get loyalty account (corrected path)
    success, data, msg = make_request("GET", "/loyalty/account", token=auth_token)
    print_test("GET /v1/loyalty/account", "PASS" if success else "FAIL", msg)
    
    # Get rewards
    success, data, msg = make_request("GET", "/loyalty/rewards", token=auth_token)
    print_test("GET /v1/loyalty/rewards", "PASS" if success else "FAIL", msg)


def test_notifications():
    print_header("NOTIFICATIONS")
    
    if not auth_token:
        print_test("Notification tests", "SKIP", "No auth token")
        return
    
    # Get notifications
    success, data, msg = make_request("GET", "/notifications", token=auth_token)
    print_test("GET /v1/notifications", "PASS" if success else "FAIL", msg)


def test_reviews():
    print_header("REVIEWS")
    
    if test_product_id:
        # Get product reviews
        success, data, msg = make_request("GET", f"/reviews/product/{test_product_id}")
        print_test("GET /v1/reviews/product/{id}", "PASS" if success else "FAIL", msg)


def test_search():
    print_header("SEARCH")
    
    # Autocomplete search
    success, data, msg = make_request("GET", "/search/autocomplete", 
                                      params={"q": "test", "type": "product", "limit": 10})
    print_test("GET /v1/search/autocomplete", "PASS" if success else "FAIL", msg)


def test_subscriptions():
    print_header("SUBSCRIPTIONS")
    
    if not auth_token:
        print_test("Subscription tests", "SKIP", "No auth token")
        return
    
    # Get subscriptions
    success, data, msg = make_request("GET", "/subscriptions", token=auth_token)
    print_test("GET /v1/subscriptions", "PASS" if success else "FAIL", msg)


def test_admin_endpoints():
    print_header("ADMIN ENDPOINTS")
    
    if not admin_token:
        print_test("Admin tests", "SKIP", "No admin token")
        return
    
    # Get admin stats
    success, data, msg = make_request("GET", "/admin/stats", token=admin_token)
    print_test("GET /v1/admin/stats", "PASS" if success else "FAIL", msg)
    
    # Get platform overview
    success, data, msg = make_request("GET", "/admin/overview", token=admin_token)
    print_test("GET /v1/admin/overview", "PASS" if success else "FAIL", msg)
    
    # Get all orders (admin)
    success, data, msg = make_request("GET", "/admin/orders", token=admin_token, 
                                      params={"page": 1, "limit": 10})
    print_test("GET /v1/admin/orders", "PASS" if success else "FAIL", msg)
    
    # Get inventory
    success, data, msg = make_request("GET", "/inventory", token=admin_token)
    print_test("GET /v1/inventory", "PASS" if success else "FAIL", msg)
    
    # Get analytics dashboard
    success, data, msg = make_request("GET", "/analytics/dashboard", token=admin_token)
    print_test("GET /v1/analytics/dashboard", "PASS" if success else "FAIL", msg)


def test_health():
    print_header("HEALTH CHECKS")
    
    # Root endpoint (use BASE_URL directly, not API_BASE)
    try:
        response = requests.get(BASE_URL + "/", timeout=10)
        success = response.status_code == 200
        msg = f"Status: {response.status_code}"
    except Exception as e:
        success = False
        msg = str(e)
    print_test("GET /", "PASS" if success else "FAIL", msg)
    
    # Liveness
    success, data, msg = make_request("GET", "/health/live")
    print_test("GET /v1/health/live", "PASS" if success else "FAIL", msg)
    
    # Readiness
    success, data, msg = make_request("GET", "/health/ready")
    print_test("GET /v1/health/ready", "PASS" if success else "FAIL", msg)


def print_summary():
    print_header("TEST SUMMARY")
    
    total = test_results["passed"] + test_results["failed"] + test_results["skipped"]
    
    print(f"{Colors.GREEN}Passed:  {test_results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}Failed:  {test_results['failed']}{Colors.RESET}")
    print(f"{Colors.YELLOW}Skipped: {test_results['skipped']}{Colors.RESET}")
    print(f"{Colors.BOLD}Total:   {total}{Colors.RESET}")
    
    if test_results["failed"] > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.RESET}")
        for error in test_results["errors"][:10]:  # Show first 10 errors
            print(f"  {Colors.RED}• {error}{Colors.RESET}")
    
    success_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.RESET}")
    
    return test_results["failed"] == 0


def main():
    print(f"\n{Colors.BOLD}Corrected API Testing Suite{Colors.RESET}")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests in order
    if not test_authentication():
        print(f"\n{Colors.RED}Authentication failed. Skipping remaining tests.{Colors.RESET}")
        sys.exit(1)
    
    test_products()
    test_cart()
    test_orders()
    test_user_management()
    test_wishlist()
    test_loyalty()
    test_notifications()
    test_reviews()
    test_search()
    test_subscriptions()
    test_admin_endpoints()
    test_health()
    
    success = print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
