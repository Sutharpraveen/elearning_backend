#!/usr/bin/env python
"""
Payment Testing Script
This script helps you test the payment gateway integration
"""
import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from users.models import CustomUser
from courses.models import Course
from payments.models import Payment

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_payment_flow():
    base_url = "http://127.0.0.1:8000"
    
    print_section("PAYMENT GATEWAY TESTING")
    
    # Step 1: Get or create a test user
    print("Step 1: Getting test user...")
    try:
        user = CustomUser.objects.first()
        if not user:
            print("❌ No users found. Please create a user first via admin or registration API")
            return
        print(f"✅ Using user: {user.email} (ID: {user.id})")
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return
    
    # Step 2: Get a course
    print("\nStep 2: Getting a course...")
    try:
        course = Course.objects.first()
        if not course:
            print("❌ No courses found. Please create a course first via admin")
            return
        print(f"✅ Using course: {course.title} (ID: {course.id})")
        print(f"   Price: ₹{course.original_price}")
    except Exception as e:
        print(f"❌ Error getting course: {e}")
        return
    
    # Step 3: Login to get JWT token
    print("\nStep 3: Getting JWT token...")
    login_url = f"{base_url}/api/users/login/"
    login_data = {
        "email": user.email,
        "password": "your_password_here"  # User needs to provide actual password
    }
    
    print(f"⚠️  You need to login first to get JWT token")
    print(f"   Login URL: {login_url}")
    print(f"   Email: {user.email}")
    print(f"   Password: [Your password]")
    print("\n   Or use this curl command:")
    print(f'   curl -X POST {login_url} \\')
    print(f'        -H "Content-Type: application/json" \\')
    print(f'        -d \'{{"email": "{user.email}", "password": "your_password"}}\'')
    
    # Step 4: Show payment endpoints
    print_section("PAYMENT API ENDPOINTS")
    
    print("1. CREATE PAYMENT ORDER:")
    print(f"   POST {base_url}/api/payments/create/")
    print("   Headers: Authorization: Bearer <your_jwt_token>")
    print("   Body:")
    print(json.dumps({
        "course_id": course.id,
        "amount": str(course.original_price),
        "currency": "INR"
    }, indent=2))
    
    print("\n2. VERIFY PAYMENT:")
    print(f"   POST {base_url}/api/payments/verify/")
    print("   Headers: Authorization: Bearer <your_jwt_token>")
    print("   Body:")
    print(json.dumps({
        "razorpay_order_id": "order_xxxxx",
        "razorpay_payment_id": "pay_xxxxx",
        "razorpay_signature": "signature_xxxxx"
    }, indent=2))
    
    # Step 5: Show existing payments
    print_section("EXISTING PAYMENTS IN DATABASE")
    payments = Payment.objects.all()[:5]
    if payments:
        for payment in payments:
            print(f"Order ID: {payment.razorpay_order_id}")
            print(f"Status: {payment.status}")
            print(f"Amount: ₹{payment.amount}")
            print(f"Course: {payment.course.title}")
            print(f"User: {payment.user.email}")
            print("-" * 40)
    else:
        print("No payments found in database")
    
    # Step 6: Test Razorpay connection
    print_section("RAZORPAY CONNECTION TEST")
    try:
        from django.conf import settings
        import razorpay
        
        if hasattr(settings, 'RAZORPAY_KEY_ID') and hasattr(settings, 'RAZORPAY_KEY_SECRET'):
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            print(f"✅ Razorpay Key ID: {settings.RAZORPAY_KEY_ID}")
            print(f"✅ Razorpay Key Secret: {'*' * len(settings.RAZORPAY_KEY_SECRET)}")
            print("✅ Razorpay client initialized successfully")
        else:
            print("❌ Razorpay keys not configured in settings")
    except Exception as e:
        print(f"❌ Error testing Razorpay connection: {e}")
    
    print_section("TESTING INSTRUCTIONS")
    print("""
To test payment flow:

1. Get JWT Token:
   POST http://127.0.0.1:8000/api/users/login/
   {
     "email": "user@example.com",
     "password": "password"
   }

2. Create Payment Order:
   POST http://127.0.0.1:8000/api/payments/create/
   Headers: Authorization: Bearer <token>
   {
     "course_id": 1,
     "amount": "999.00",
     "currency": "INR"
   }

3. Use the order_id from step 2 in Razorpay test payment
   Test Card: 4111 1111 1111 1111
   CVV: Any 3 digits
   Expiry: Any future date

4. Verify Payment:
   POST http://127.0.0.1:8000/api/payments/verify/
   Headers: Authorization: Bearer <token>
   {
     "razorpay_order_id": "order_xxxxx",
     "razorpay_payment_id": "pay_xxxxx",
     "razorpay_signature": "signature_xxxxx"
   }
    """)

if __name__ == "__main__":
    test_payment_flow()



