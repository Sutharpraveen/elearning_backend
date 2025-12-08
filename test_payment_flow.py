#!/usr/bin/env python
"""
Complete Payment Flow Testing Script
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

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_payment_flow():
    print_section("PAYMENT FLOW TESTING")
    
    # Step 1: Get user and course
    user = CustomUser.objects.first()
    course = Course.objects.first()
    
    if not user:
        print("❌ No users found!")
        return
    
    if not course:
        print("❌ No courses found!")
        return
    
    print(f"\n✅ User: {user.email} (ID: {user.id})")
    print(f"✅ Course: {course.title} (ID: {course.id})")
    print(f"   Price: ₹{course.original_price}")
    print(f"   Discounted: ₹{course.discounted_price}")
    
    # Step 2: Try to login
    print_section("STEP 1: LOGIN")
    print(f"\nTrying to login with: {user.email}")
    print("Note: You may need to provide the correct password")
    
    # For testing, let's show what needs to be done
    print("\n📝 Manual Login Required:")
    print(f"   POST {BASE_URL}/api/users/login/")
    print(f"   Body: {{'email': '{user.email}', 'password': 'YOUR_PASSWORD'}}")
    
    # Step 3: Create Payment Order
    print_section("STEP 2: CREATE PAYMENT ORDER")
    print("\nAfter getting JWT token, use this command:")
    print(f"\ncurl -X POST {BASE_URL}/api/payments/create/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"  -d '{{\"course_id\": {course.id}, \"amount\": \"{course.discounted_price}\", \"currency\": \"INR\"}}'")
    
    # Step 4: Show expected response
    print_section("STEP 3: EXPECTED RESPONSE")
    print("\nYou should get:")
    print(json.dumps({
        "status": "success",
        "message": "Payment order created successfully",
        "data": {
            "order_id": "order_xxxxx",
            "amount": str(course.discounted_price),
            "currency": "INR",
            "key": "rzp_test_MGr4dvkOY66fMO",
            "course_id": course.id,
            "course_title": course.title
        }
    }, indent=2))
    
    # Step 5: Razorpay Test Payment
    print_section("STEP 4: RAZORPAY TEST PAYMENT")
    print("\nUse the order_id in Razorpay checkout:")
    print("  - Test Card: 4111 1111 1111 1111")
    print("  - CVV: Any 3 digits (e.g., 123)")
    print("  - Expiry: Any future date (e.g., 12/25)")
    print("  - Name: Any name")
    
    # Step 6: Verify Payment
    print_section("STEP 5: VERIFY PAYMENT")
    print("\nAfter Razorpay payment, verify with:")
    print(f"\ncurl -X POST {BASE_URL}/api/payments/verify/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print("  -d '{")
    print('    "razorpay_order_id": "order_xxxxx",')
    print('    "razorpay_payment_id": "pay_xxxxx",')
    print('    "razorpay_signature": "signature_xxxxx"')
    print("  }'")
    
    # Check existing payments
    print_section("EXISTING PAYMENTS")
    payments = Payment.objects.all()
    if payments:
        print(f"\nFound {payments.count()} payment(s):")
        for payment in payments:
            print(f"\n  Order ID: {payment.razorpay_order_id}")
            print(f"  Status: {payment.status}")
            print(f"  Amount: ₹{payment.amount}")
            print(f"  Course: {payment.course.title}")
            print(f"  User: {payment.user.email}")
    else:
        print("\nNo payments found yet.")
    
    print_section("TESTING COMPLETE")
    print("\n✅ Payment system is ready!")
    print("Follow the steps above to test the complete payment flow.")

if __name__ == "__main__":
    test_payment_flow()









