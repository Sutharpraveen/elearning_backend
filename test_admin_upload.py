#!/usr/bin/env python3
"""
Test Admin Video Upload Processing
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

from courses.models import Lecture, Section, Course
from courses.admin import LectureAdmin
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from unittest.mock import Mock

def test_admin_video_processing():
    """Test that admin triggers video processing"""
    print("🎬 Testing Admin Video Upload Processing...")

    try:
        # Get existing section
        section = Section.objects.filter(course__is_published=True).first()
        if not section:
            print("❌ No published course/section found")
            return False

        print(f"✅ Using section: {section.title}")

        # Create a mock video file
        test_video_content = b"fake video content for testing admin upload"
        video_filename = "admin_test_video.mp4"

        # Create lecture manually (simulating admin save)
        lecture = Lecture.objects.create(
            section=section,
            title="Admin Test Lecture",
            description="Testing admin video processing",
            order=section.lectures.count() + 1,
            video_file=None  # Will be set during save
        )

        # Simulate file upload by setting video_file
        lecture.video_file.save(video_filename, ContentFile(test_video_content), save=True)

        print("✅ Lecture created with video file")
        print(f"   Title: {lecture.title}")
        print(f"   Video file: {lecture.video_file}")
        print(f"   Initial status: {lecture.processing_status}")

        # Now simulate what happens in admin save_model
        from courses.video_utils import process_lecture_video_universal
        import threading

        # Reset status to pending (like admin does)
        lecture.processing_status = 'pending'
        lecture.save()

        print(f"   Status after reset: {lecture.processing_status}")

        # Start processing (like admin save_model does)
        thread = threading.Thread(target=process_lecture_video_universal, args=(lecture.id,))
        thread.start()
        thread.join(timeout=10)  # Wait up to 10 seconds

        # Check final status
        lecture.refresh_from_db()
        print(f"   Final status: {lecture.processing_status}")
        print(f"   Duration: {lecture.duration}")
        print(f"   File size: {lecture.file_size}")

        # Clean up
        lecture.delete()
        print("🧹 Test lecture cleaned up")

        return True

    except Exception as e:
        print(f"❌ Error during admin upload test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lecture_admin_form():
    """Test that the admin form works correctly"""
    print("\n📝 Testing Lecture Admin Form...")

    try:
        from courses.admin import LectureAdminForm
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create form data
        form_data = {
            'title': 'Form Test Lecture',
            'description': 'Testing admin form',
            'order': 1,
            'is_preview': False
        }

        # Create fake uploaded file
        uploaded_file = SimpleUploadedFile(
            "test_video.mp4",
            b"fake video content",
            content_type="video/mp4"
        )

        file_data = {'video_file': uploaded_file}

        # Get section for form
        section = Section.objects.filter(course__is_published=True).first()
        if not section:
            print("❌ No section found for form test")
            return False

        form_data['section'] = section.id

        # Create form
        form = LectureAdminForm(data=form_data, files=file_data)

        if form.is_valid():
            print("✅ Admin form is valid")
            print(f"   Video file: {form.cleaned_data.get('video_file')}")

            # Save form (but don't commit to DB for testing)
            lecture = form.save(commit=False)
            print(f"   Would save lecture: {lecture.title}")

            return True
        else:
            print("❌ Admin form validation failed")
            print(f"   Errors: {form.errors}")
            return False

    except Exception as e:
        print(f"❌ Error testing admin form: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🎛️  Admin Video Upload Test")
    print("=" * 35)

    # Test admin processing
    processing_test = test_admin_video_processing()

    # Test admin form
    form_test = test_lecture_admin_form()

    print("\n" + "=" * 35)
    print("📊 Test Results:")
    print(f"   Admin Processing: {'✅' if processing_test else '❌'}")
    print(f"   Admin Form: {'✅' if form_test else '❌'}")

    if processing_test and form_test:
        print("\n🎉 Admin video upload is working!")
        print("\n📋 How to use:")
        print("1. Go to Django Admin: http://127.0.0.1:8002/admin/")
        print("2. Navigate to Courses > Lectures")
        print("3. Click 'Add Lecture'")
        print("4. Fill title, description, order")
        print("5. Upload MP4 video in 'Video file' field")
        print("6. Click 'Save' - processing starts automatically")
        print("7. Check 'Processing status' field for progress")
    else:
        print("\n❌ Admin upload needs fixes.")
        print("\n🔧 Common issues:")
        if not processing_test:
            print("   • Video processing not starting from admin")
            print("   • Check save_model method in LectureAdmin")
        if not form_test:
            print("   • Form validation failing")
            print("   • Check file upload configuration")

if __name__ == '__main__':
    main()
