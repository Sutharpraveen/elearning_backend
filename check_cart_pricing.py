#!/usr/bin/env python3
"""
Check Cart Pricing Logic
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
django.setup()

from courses.models import Course
from shopping.models import CartItem

def check_cart_pricing():
    """Check cart pricing logic"""

    print("🛒 Cart Pricing Analysis")
    print("=" * 40)

    # Find the course mentioned in the cart data
    courses = Course.objects.filter(title__icontains='sdfsdafsd')
    if courses.exists():
        course = courses.first()
        print(f"📚 Course Found: '{course.title}'")
        print(f"   Current Original Price: ${course.original_price}")
        print(f"   Current Discounted Price: ${course.discounted_price or 'None'}")
        print(f"   Course ID: {course.id}")

        # Check all cart items for this course
        cart_items = CartItem.objects.filter(course=course).select_related('cart__user')

        print(f"\n🛍️  Cart Items Analysis ({cart_items.count()} items):")
        print("-" * 50)

        for i, item in enumerate(cart_items, 1):
            user = item.cart.user
            print(f"{i}. User: {user.username} ({user.email})")
            print(f"   Original Price in Cart: ${item.original_price}")
            print(f"   Price at Time of Adding: ${item.price_at_time_of_adding}")
            print(f"   Discount %: {item.discount_percentage}%")
            print(f"   Savings: ${item.savings}")
            print(f"   Added at: {item.added_at}")
            print(f"   Saved for Later: {item.is_saved_for_later}")
            print()

        # Analysis
        prices = [item.original_price for item in cart_items]
        if len(set(prices)) > 1:
            print("⚠️  ISSUE FOUND: Different users have different original prices!")
            print(f"   Price range: ${min(prices)} - ${max(prices)}")
            print("   This happens when course price changes after cart addition.")
        else:
            print("✅ All cart items have consistent pricing.")

    else:
        print("❌ Course 'sdfsdafsd' not found.")
        print("\n📚 All available courses:")
        all_courses = Course.objects.all()
        for course in all_courses:
            print(f"   {course.id}: '{course.title}' - ${course.original_price}")

    print("\n🔍 Cart Logic Explanation:")
    print("=" * 40)
    print("1. When user adds course to cart:")
    print("   - original_price = course.original_price (at that time)")
    print("   - price_at_time_of_adding = course.discounted_price or original_price")
    print("   - discount_percentage = calculated based on price difference")
    print()
    print("2. If course price changes AFTER cart addition:")
    print("   - New users see new price")
    print("   - Old cart items keep old price")
    print("   - This creates different 'original_price' values")
    print()
    print("3. This is NORMAL behavior for e-commerce!")
    print("   - Protects users from price increases")
    print("   - Allows price decreases to benefit users")

if __name__ == '__main__':
    check_cart_pricing()
