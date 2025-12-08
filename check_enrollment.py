#!/usr/bin/env python
"""
Enrollment Check Script
Database में enrollment check करने के लिए
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from courses.models import Enrollment, Course
from users.models import CustomUser
from payments.models import Payment

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_enrollments():
    print_section("ENROLLMENT DATABASE CHECK")
    
    # Check all enrollments
    enrollments = Enrollment.objects.all()
    print(f'\n📚 Total Enrollments: {enrollments.count()}')
    
    if enrollments.count() > 0:
        print('\n' + '-'*60)
        print('ENROLLMENT DETAILS:')
        print('-'*60)
        for i, enrollment in enumerate(enrollments, 1):
            print(f'\n{i}. Enrollment ID: {enrollment.id}')
            print(f'   👤 User: {enrollment.user.email} (ID: {enrollment.user.id})')
            print(f'   📚 Course: {enrollment.course.title} (ID: {enrollment.course.id})')
            print(f'   📅 Enrolled At: {enrollment.enrolled_at}')
            print(f'   ✅ Completed: {enrollment.completed}')
            print(f'   🕐 Last Accessed: {enrollment.last_accessed or "Never"}')
            print('-'*60)
    else:
        print('\n⚠️  No enrollments found in database')
        print('   This means no user has enrolled in any course yet')
    
    # Check payments
    print_section("PAYMENT RECORDS")
    payments = Payment.objects.all()
    print(f'\n💳 Total Payments: {payments.count()}')
    
    if payments.count() > 0:
        print('\n' + '-'*60)
        for i, payment in enumerate(payments, 1):
            print(f'\n{i}. Payment ID: {payment.id}')
            print(f'   Order ID: {payment.razorpay_order_id}')
            print(f'   👤 User: {payment.user.email}')
            print(f'   📚 Course: {payment.course.title}')
            print(f'   💰 Amount: ₹{payment.amount}')
            print(f'   📊 Status: {payment.status}')
            print(f'   📅 Created: {payment.created_at}')
            
            # Check if enrollment exists for this payment
            enrollment_exists = Enrollment.objects.filter(
                user=payment.user,
                course=payment.course
            ).exists()
            
            if payment.status == 'completed':
                if enrollment_exists:
                    print(f'   ✅ Enrollment: YES (User is enrolled)')
                else:
                    print(f'   ❌ Enrollment: NO (Payment completed but no enrollment!)')
            else:
                print(f'   ⏳ Payment Status: {payment.status} (Enrollment will happen after verification)')
            print('-'*60)
    else:
        print('\n⚠️  No payments found in database')
    
    # Summary
    print_section("SUMMARY")
    print(f'Total Users: {CustomUser.objects.count()}')
    print(f'Total Courses: {Course.objects.count()}')
    print(f'Total Enrollments: {enrollments.count()}')
    print(f'Total Payments: {payments.count()}')
    
    completed_payments = Payment.objects.filter(status='completed').count()
    if completed_payments > 0:
        print(f'\n✅ Completed Payments: {completed_payments}')
        print(f'✅ Enrollments: {enrollments.count()}')
        if completed_payments == enrollments.count():
            print('\n✅ All completed payments have enrollments!')
        else:
            print(f'\n⚠️  Warning: {completed_payments - enrollments.count()} completed payment(s) without enrollment')
    
    # Show how to manually create enrollment for testing
    print_section("MANUAL ENROLLMENT FOR TESTING")
    print('\n💡 Agar aap manually enrollment test karna chahte hain:')
    print('\nPython script se:')
    print('''
from courses.models import Enrollment, Course
from users.models import CustomUser

# Get user and course
user = CustomUser.objects.get(email='p@gmail.com')
course = Course.objects.get(id=1)

# Create enrollment
enrollment, created = Enrollment.objects.get_or_create(
    user=user,
    course=course
)

if created:
    print(f'✅ Enrollment created: {user.email} enrolled in {course.title}')
else:
    print(f'⚠️  Enrollment already exists')
    ''')
    
    print('\nOr API se (after payment verification):')
    print('POST http://127.0.0.1:8000/api/payments/verify/')
    print('(This will automatically create enrollment)')

if __name__ == "__main__":
    check_enrollments()









