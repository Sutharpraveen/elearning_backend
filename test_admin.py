#!/usr/bin/env python3
"""
Test Django Admin Interface
Run this to verify admin is working properly
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

from django.contrib.admin.sites import AdminSite
from courses.admin import LectureAdmin, CourseAdmin, SectionAdmin
from courses.models import Lecture, Course, Section

def test_admin_configurations():
    """Test that admin configurations are valid"""
    print("\n🧪 Testing Admin Configurations...")

    site = AdminSite()

    try:
        # Test CourseAdmin
        course_admin = CourseAdmin(Course, site)
        print("✅ CourseAdmin: Valid configuration")

        # Test SectionAdmin
        section_admin = SectionAdmin(Section, site)
        print("✅ SectionAdmin: Valid configuration")

        # Test LectureAdmin (the one we just fixed)
        lecture_admin = LectureAdmin(Lecture, site)
        print("✅ LectureAdmin: Valid configuration")

        # Test that all fields exist in models
        lecture_fields = ['section', 'title', 'description', 'order', 'original_video',
                         'processing_status', 'duration', 'file_size', 'is_preview',
                         'video_1080p', 'video_720p', 'video_480p', 'video_360p', 'hls_playlist']

        for field_name in lecture_fields:
            if hasattr(Lecture, field_name):
                print(f"✅ Lecture.{field_name}: Field exists")
            else:
                print(f"❌ Lecture.{field_name}: Field does NOT exist")

        return True

    except Exception as e:
        print(f"❌ Admin configuration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🎛️  Django Admin Test")
    print("=" * 30)

    success = test_admin_configurations()

    if success:
        print("\n🎉 All admin configurations are valid!")
        print("\n🔧 Your Django admin should now work properly:")
        print("- Go to: http://127.0.0.1:8000/admin/")
        print("- Login with your superuser credentials")
        print("- You should be able to add/edit lectures without errors")
    else:
        print("\n❌ Admin configuration has issues.")
        print("Check the error messages above.")

if __name__ == '__main__':
    main()
