#!/usr/bin/env python3
"""
Complete Shopping/Cart Functionality Test
"""

import requests
import json

# Configuration
SERVER_URL = "http://127.0.0.1:8002"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY1OTE4OTIzLCJpYXQiOjE3NjU5MTUzMjMsImp0aSI6ImY0ZjU2NDIxMTY2MTQyMzg5NjY2OWU5NThhOWUyZDVjIiwidXNlcl9pZCI6MX0.e9r6F6crsAz241g9mzmbbpK5Pb5EI0Hs4Wj23uArmZg"

def make_request(method, endpoint, data=None):
    """Make HTTP request with JWT token"""
    headers = {
        'Authorization': f'Bearer {JWT_TOKEN}',
        'Content-Type': 'application/json'
    }

    url = f"{SERVER_URL}{endpoint}"

    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)

        return response.status_code, response.json() if response.content else {}
    except Exception as e:
        return None, str(e)

def test_shopping_functionality():
    """Test all shopping/cart functionality"""
    print("🛒 Complete Shopping/Cart Functionality Test")
    print("=" * 55)

    results = {}

    # Test 1: Cart Summary
    print("\n1️⃣  Testing Cart Summary...")
    status, data = make_request('GET', '/api/shopping/cart/get_cart_summary/')
    if status == 200:
        results['cart_summary'] = '✅ PASS'
        cart_data = data.get('data', {})
        print(f"   ✅ Cart: {cart_data.get('total_items', 0)} items, ${cart_data.get('total_price', 0)}")
    else:
        results['cart_summary'] = f'❌ FAIL ({status})'
        print(f"   ❌ Cart summary failed: {data}")

    # Test 2: Wishlist
    print("\n2️⃣  Testing Wishlist...")
    status, data = make_request('GET', '/api/shopping/wishlist/')
    if status == 200:
        results['wishlist'] = '✅ PASS'
        print("   ✅ Wishlist accessible")
    else:
        results['wishlist'] = f'❌ FAIL ({status})'
        print(f"   ❌ Wishlist failed: {data}")

    # Test 3: Add to Cart
    print("\n3️⃣  Testing Add to Cart...")
    status, data = make_request('POST', '/api/shopping/cart/add/', {'course_id': 1})
    if status == 201:
        results['add_to_cart'] = '✅ PASS'
        print("   ✅ Course added to cart successfully")
    elif status == 400 and 'already in cart' in str(data).lower():
        results['add_to_cart'] = '⚠️  PASS (Already in cart)'
        print("   ⚠️  Course already in cart (expected)")
    else:
        results['add_to_cart'] = f'❌ FAIL ({status})'
        print(f"   ❌ Add to cart failed: {data}")

    # Test 4: Get Saved Items
    print("\n4️⃣  Testing Get Saved Items...")
    status, data = make_request('GET', '/api/shopping/cart/get_saved_items/')
    if status == 200:
        results['saved_items'] = '✅ PASS'
        saved_count = data.get('data', {}).get('total_saved_items', 0)
        print(f"   ✅ Saved items: {saved_count} items")
    else:
        results['saved_items'] = f'❌ FAIL ({status})'
        print(f"   ❌ Saved items failed: {data}")

    # Test 5: Course Status Check
    print("\n5️⃣  Testing Course Status Check...")
    status, data = make_request('GET', '/api/shopping/course-status/1/')
    if status == 200:
        results['course_status'] = '✅ PASS'
        print(f"   ✅ Course status: in_cart={data.get('in_cart')}, in_wishlist={data.get('in_wishlist')}")
    else:
        results['course_status'] = f'❌ FAIL ({status})'
        print(f"   ❌ Course status failed: {data}")

    # Test 6: Add to Wishlist
    print("\n6️⃣  Testing Add to Wishlist...")
    status, data = make_request('POST', '/api/shopping/wishlist/add_course/', {'course_id': 1})
    if status == 200:
        results['add_to_wishlist'] = '✅ PASS'
        print("   ✅ Course added to wishlist")
    elif status == 200 and 'already in wishlist' in str(data).lower():
        results['add_to_wishlist'] = '⚠️  PASS (Already in wishlist)'
        print("   ⚠️  Course already in wishlist (expected)")
    else:
        results['add_to_wishlist'] = f'❌ FAIL ({status})'
        print(f"   ❌ Add to wishlist failed: {data}")

    # Test 7: Move to Cart from Wishlist
    print("\n7️⃣  Testing Move to Cart from Wishlist...")
    status, data = make_request('POST', '/api/shopping/wishlist/move_to_cart/', {'course_id': 1})
    if status == 200:
        results['move_to_cart'] = '✅ PASS'
        print("   ✅ Course moved to cart from wishlist")
    else:
        results['move_to_cart'] = f'❌ FAIL ({status})'
        print(f"   ❌ Move to cart failed: {data}")

    # Test 8: Remove from Cart
    print("\n8️⃣  Testing Remove from Cart...")
    status, data = make_request('POST', '/api/shopping/cart/remove/', {'course_id': 1})
    if status == 200:
        results['remove_from_cart'] = '✅ PASS'
        print("   ✅ Course removed from cart")
    else:
        results['remove_from_cart'] = f'❌ FAIL ({status})'
        print(f"   ❌ Remove from cart failed: {data}")

    # Final Cart Summary
    print("\n📊 Final Cart Summary:")
    status, data = make_request('GET', '/api/shopping/cart/get_cart_summary/')
    if status == 200:
        cart_data = data.get('data', {})
        print(f"   Items: {cart_data.get('total_items', 0)}")
        print(f"   Subtotal: ${cart_data.get('subtotal', 0)}")
        print(f"   Total: ${cart_data.get('total_price', 0)}")

    # Summary
    print("\n" + "=" * 55)
    print("📋 TEST RESULTS SUMMARY:")
    print("=" * 55)

    all_pass = True
    for test_name, result in results.items():
        print(f"   {test_name.replace('_', ' ').title()}: {result}")
        if 'FAIL' in result:
            all_pass = False

    print("\n" + "=" * 55)
    if all_pass:
        print("🎉 ALL SHOPPING/CART FUNCTIONALITY WORKING PERFECTLY!")
        print("✅ Add to Cart, Wishlist, Cart Summary, Saved Items - सब काम कर रहा है!")
    else:
        print("⚠️  कुछ functionality में issues हैं। ऊपर check करें।")

    return results

if __name__ == '__main__':
    test_shopping_functionality()
