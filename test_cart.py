#!/usr/bin/env python3
"""
Test Cart Functionality
Run this to test cart add and get_cart_summary endpoints
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

from django.contrib.auth import get_user_model
from shopping.models import Cart, CartItem
from shopping.serializers import CartSummarySerializer, CartItemSerializer
from courses.models import Course
from django.test import RequestFactory

def test_cart_functionality():
    """Test cart creation and serialization"""
    print("\n🛒 Testing Cart Functionality...")

    try:
        # Get a user
        User = get_user_model()
        user = User.objects.filter(role='student').first()
        if not user:
            print("❌ No student user found. Create a student user first.")
            return False

        print(f"✅ Found user: {user.email}")

        # Get a course
        course = Course.objects.filter(is_published=True).first()
        if not course:
            print("❌ No published course found. Create and publish a course first.")
            return False

        print(f"✅ Found course: {course.title} (Price: ${course.original_price})")

        # Create or get cart
        cart, created = Cart.objects.get_or_create(user=user)
        print(f"✅ Cart {'created' if created else 'found'}: {cart}")

        # Test cart summary serialization
        try:
            factory = RequestFactory()
            request = factory.get('/')
            request.user = user

            serializer = CartSummarySerializer(cart, context={'request': request})
            cart_data = serializer.data
            print("✅ Cart summary serialization successful")
            print(f"   Items: {cart_data['total_items']}")
            print(f"   Subtotal: ${cart_data['subtotal']}")
            print(f"   Total: ${cart_data['total_price']}")
        except Exception as e:
            print(f"❌ Cart summary serialization failed: {e}")
            return False

        # Test adding item to cart
        try:
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                course=course,
                defaults={
                    'original_price': course.original_price,
                    'price_at_time_of_adding': course.discounted_price or course.original_price,
                    'discount_percentage': ((course.original_price - (course.discounted_price or course.original_price)) / course.original_price) * 100 if course.discounted_price else 0
                }
            )

            if created:
                print("✅ Cart item created successfully")
            else:
                print("✅ Cart item already exists")

            # Test cart item serialization
            serializer = CartItemSerializer(cart_item, context={'request': request})
            item_data = serializer.data
            print("✅ Cart item serialization successful")
            print(f"   Course: {item_data['course']['title']}")
            print(f"   Price: ${item_data['price_at_time_of_adding']}")
            print(f"   Savings: ${item_data['savings']}")

        except Exception as e:
            print(f"❌ Cart item creation/serialization failed: {e}")
            return False

        # Clean up test data
        if created:
            cart_item.delete()
            print("🧹 Test cart item cleaned up")

        return True

    except Exception as e:
        print(f"❌ Error during cart testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🛒 E-Learning Cart Test")
    print("=" * 30)

    success = test_cart_functionality()

    if success:
        print("\n🎉 Cart functionality is working!")
        print("\n🔧 If you're still getting errors in your API:")
        print("1. Check authentication (JWT token)")
        print("2. Verify course exists and is published")
        print("3. Check server logs for detailed errors")
        print("4. Test with curl commands:")
        print("   curl -H 'Authorization: Bearer YOUR_TOKEN' http://your-server:8000/api/shopping/cart/get_cart_summary/")
    else:
        print("\n❌ Cart functionality has issues.")
        print("Check the error messages above and fix them.")

if __name__ == '__main__':
    main()
