import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from rest_framework.test import APIClient
from users.models import CustomUser
from courses.models import Course, Category
from payments.models import MultiPayment
from shopping.models import Cart, CartItem
import unittest.mock

# Create or get user
user = CustomUser.objects.filter(email='test@example.com').first()
if not user:
    user = CustomUser.objects.create(username='tester', email='test@example.com')

# Create or get category
cat = Category.objects.first()
if not cat:
    cat = Category.objects.create(name="Test Category", is_active=True)

# Create 2 courses with unique slugs
c1 = Course.objects.filter(slug='course-a').first()
if not c1:
    c1 = Course.objects.create(title="Course A", slug="course-a", instructor=user, category=cat, original_price=10)

c2 = Course.objects.filter(slug='course-b').first()
if not c2:
    c2 = Course.objects.create(title="Course B", slug="course-b", instructor=user, category=cat, original_price=20)

client = APIClient()
client.force_authenticate(user=user)

# Add to cart to simulate real environment
cart, _ = Cart.objects.get_or_create(user=user)
CartItem.objects.get_or_create(cart=cart, course=c1)
CartItem.objects.get_or_create(cart=cart, course=c2)

print("\n--- STEP 1: Creating Multi Payment Order ---")
# Mock razorpay order create since we don't need to hit real Razorpay
with unittest.mock.patch('payments.views.client.order.create', return_value={'id': 'order_MOCK123'}):
    create_resp = client.post('/api/payments/multi/create/', {'course_ids': [c1.id, c2.id]}, format='json')
    print(f"Status: {create_resp.status_code}")
    print(f"Response: {create_resp.data}")

if create_resp.status_code == 200:
    order_id = create_resp.data['data']['order_id']
    print(f"\n--- STEP 2: Verifying Multi Payment Order ({order_id}) ---")
    
    # Mock signature verification
    with unittest.mock.patch('payments.views.client.utility.verify_payment_signature', return_value=True):
        verify_resp = client.post('/api/payments/multi/verify/', {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': 'pay_MOCK123',
            'razorpay_signature': 'valid_mock_signature_123'
        }, format='json')
        
        print(f"Status: {verify_resp.status_code}")
        print(f"Response: {verify_resp.data}")
        
        if verify_resp.status_code == 200:
            print("\n✅ Verification Successful!")
            # Check if enrolled
            enrolled_c1 = user.enrollments.filter(course=c1).exists()
            enrolled_c2 = user.enrollments.filter(course=c2).exists()
            print(f"Enrolled in {c1.title}? {enrolled_c1}")
            print(f"Enrolled in {c2.title}? {enrolled_c2}")
            # Check cart is empty of those courses
            cart_has_c1 = CartItem.objects.filter(cart=cart, course=c1).exists()
            cart_has_c2 = CartItem.objects.filter(cart=cart, course=c2).exists()
            print(f"Course A removed from Cart? {not cart_has_c1}")
            print(f"Course B removed from Cart? {not cart_has_c2}")
