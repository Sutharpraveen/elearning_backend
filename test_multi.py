import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.test import RequestFactory
from payments.views import verify_multi_payment
from users.models import CustomUser
from payments.models import MultiPayment
from courses.models import Course, Category

user = CustomUser.objects.first()
if not user:
    user = CustomUser.objects.create(username="testuser", email="test@test.com")

cat = Category.objects.first()
if not cat:
    cat = Category.objects.create(name="TestCat", is_active=True)

c1 = Course.objects.first()
if getattr(c1, 'title', None) != 'C1':
    c1 = Course.objects.create(title="C1", slug="c1-test", instructor=user, category=cat, level="Beginner", original_price=10)

c2 = Course.objects.last()
if getattr(c2, 'title', None) != 'C2' or c1 == c2:
    c2 = Course.objects.create(title="C2", slug="c2-test", instructor=user, category=cat, level="Beginner", original_price=20)

mp = MultiPayment.objects.create(user=user, razorpay_order_id="order_123", amount=30)
mp.courses.set([c1, c2])

# Using patch for razorpay signature verify
import unittest.mock
with unittest.mock.patch('payments.views.client.utility.verify_payment_signature', return_value=True):
    factory = RequestFactory()
    request = factory.post('/api/payments/multi/verify/', {
        'razorpay_order_id': 'order_123',
        'razorpay_payment_id': 'pay_123',
        'razorpay_signature': 'valid_sig'
    }, format='json')
    request.user = user

    response = verify_multi_payment(request)
    print("Response Status Code:", response.status_code)
    print("Response Data:", response.data)
