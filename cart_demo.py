#!/usr/bin/env python3
"""
Cart API Demo - Empty vs Filled Cart
"""

import requests
import json

def demo_cart_api():
    """Demo cart API with empty and filled states"""

    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY1OTE4OTIzLCJpYXQiOjE3NjU5MTUzMjMsImp0aSI6ImY0ZjU2NDIxMTY2MTQyMzg5NjY2OWU5NThhOWUyZDVjIiwidXNlcl9pZCI6MX0.e9r6F6crsAz241g9mzmbbpK5Pb5EI0Hs4Wj23uArmZg"

    headers = {'Authorization': f'Bearer {token}'}

    print("🛒 Cart API Demo - Empty vs Filled Cart")
    print("=" * 50)

    print("\n📭 CURRENT CART STATUS (Empty):")
    response = requests.get('http://127.0.0.1:8002/api/shopping/cart/get_cart_summary/', headers=headers)

    if response.status_code == 200:
        data = response.json()['data']
        print(f"✅ Status: {response.json()['status']}")
        print(f"📊 Total Items: {data['total_items']}")
        print(f"💰 Total Price: ${data['total_price']}")
        print(f"📦 Items Array: {len(data['items'])} items")

        if data['total_items'] == 0:
            print("✅ This is the response you showed - EMPTY CART ✅")
        else:
            print("ℹ️  Cart has items already")

    print("\n🛍️  ADDING COURSE TO CART...")
    add_response = requests.post(
        'http://127.0.0.1:8002/api/shopping/cart/add/',
        headers=headers,
        json={'course_id': 1}
    )

    if add_response.status_code == 201:
        print("✅ Course added to cart successfully!")

        print("\n📦 CART WITH ITEMS (Full Response):")
        response = requests.get('http://127.0.0.1:8002/api/shopping/cart/get_cart_summary/', headers=headers)

        if response.status_code == 200:
            cart_data = response.json()
            data = cart_data['data']

            print(f"✅ Status: {cart_data['status']}")
            print(f"📊 Total Items: {data['total_items']}")
            print(f"💰 Subtotal: ${data['subtotal']}")
            print(f"🏷️  Item Discount: ${data['item_discount_amount']}")
            print(f"🎫  Coupon Discount: ${data['coupon_discount_amount']}")
            print(f"💵  Total Price: ${data['total_price']}")
            print(f"📦 Items Array: {len(data['items'])} items")

            if data['items']:
                print("\n🛍️  ITEMS DETAILS:")
                for i, item in enumerate(data['items'], 1):
                    course = item['course']
                    print(f"  {i}. {course['title']}")
                    print(f"     Price: ${course['price']}")
                    print(f"     Quantity: {item['quantity']}")
                    print(f"     Saved for Later: {item['is_saved_for_later']}")

        print("\n📋 FULL JSON RESPONSE:")
        print(json.dumps(cart_data, indent=2))

    else:
        print(f"❌ Failed to add course: {add_response.status_code}")
        print(f"Response: {add_response.text}")

if __name__ == '__main__':
    demo_cart_api()
