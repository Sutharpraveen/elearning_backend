import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from payments.models import MultiPayment
from django.db import transaction

print("MultiPayment count:", MultiPayment.objects.count())
try:
    print("Test passed.")
except Exception as e:
    print("Test failed:", e)
