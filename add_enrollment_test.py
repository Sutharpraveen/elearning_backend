#!/usr/bin/env python
"""
Manual Enrollment Test Script
Enrollment manually add karne ke liye
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from courses.models import Enrollment, Course
from users.models import CustomUser

print('='*60)
print('MANUAL ENROLLMENT TEST')
print('='*60)

# Get user and course
user = CustomUser.objects.first()
course = Course.objects.first()

if not user:
    print('❌ No user found!')
    exit()

if not course:
    print('❌ No course found!')
    exit()

print(f'\n👤 User: {user.email}')
print(f'📚 Course: {course.title}')

# Check if enrollment already exists
existing = Enrollment.objects.filter(user=user, course=course).first()

if existing:
    print(f'\n⚠️  Enrollment already exists!')
    print(f'   Enrollment ID: {existing.id}')
    print(f'   Enrolled At: {existing.enrolled_at}')
    print(f'   Completed: {existing.completed}')
else:
    # Create enrollment
    enrollment = Enrollment.objects.create(
        user=user,
        course=course
    )
    print(f'\n✅ Enrollment created successfully!')
    print(f'   Enrollment ID: {enrollment.id}')
    print(f'   User: {enrollment.user.email}')
    print(f'   Course: {enrollment.course.title}')
    print(f'   Enrolled At: {enrollment.enrolled_at}')

# Show all enrollments
print('\n' + '='*60)
print('ALL ENROLLMENTS')
print('='*60)
enrollments = Enrollment.objects.all()
print(f'\nTotal: {enrollments.count()}')

for i, enr in enumerate(enrollments, 1):
    print(f'\n{i}. {enr.user.email} → {enr.course.title}')
    print(f'   ID: {enr.id}, Enrolled: {enr.enrolled_at}')

print('\n' + '='*60)



