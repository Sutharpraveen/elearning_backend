#!/usr/bin/env python3
"""
Test script to verify lecture creation functionality
Run this on your server to test lecture creation
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
from courses.models import Course, Section, Lecture
from django.core.files.base import ContentFile

def test_lecture_creation():
    """Test lecture creation functionality"""
    print("\n📝 Testing Lecture Creation...")

    try:
        # Get instructor user
        User = get_user_model()
        instructor = User.objects.filter(role='instructor').first()

        if not instructor:
            print("❌ No instructor found. Create an instructor user first.")
            return False

        print(f"✅ Found instructor: {instructor.email}")

        # Get a course
        course = Course.objects.filter(instructor=instructor).first()
        if not course:
            print("❌ No course found for this instructor. Create a course first.")
            return False

        print(f"✅ Found course: {course.title}")

        # Get a section
        section = course.sections.first()
        if not section:
            print("❌ No section found in course. Create a section first.")
            return False

        print(f"✅ Found section: {section.title}")

        # Create a test lecture
        lecture_data = {
            'title': 'Test Lecture',
            'description': 'This is a test lecture to verify functionality',
            'order': section.lectures.count() + 1
        }

        lecture = Lecture.objects.create(section=section, **lecture_data)
        print(f"✅ Lecture created successfully: {lecture.title} (ID: {lecture.id})")

        # Test file upload (create a dummy video file)
        test_video_content = b"dummy video content for testing"
        lecture.original_video.save(
            f'test_lecture_{lecture.id}.mp4',
            ContentFile(test_video_content),
            save=True
        )
        print(f"✅ Test video file uploaded to: {lecture.original_video.path}")

        # Check media directories
        media_root = django.conf.settings.MEDIA_ROOT
        required_dirs = [
            'lecture_videos/original',
            'lecture_videos/1080p',
            'lecture_videos/720p',
            'lecture_videos/480p',
            'lecture_videos/360p',
            'lecture_videos/hls'
        ]

        print("\n📁 Checking media directories:")
        for dir_path in required_dirs:
            full_path = os.path.join(media_root, dir_path)
            if os.path.exists(full_path):
                writable = os.access(full_path, os.W_OK)
                print(f"✅ {dir_path}: {'Writable' if writable else 'Not writable'}")
            else:
                print(f"❌ {dir_path}: Does not exist")

        # Clean up test lecture
        lecture.delete()
        print("🧹 Test lecture cleaned up")

        return True

    except Exception as e:
        print(f"❌ Error during lecture creation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🎬 E-Learning Lecture Creation Test")
    print("===================================")

    success = test_lecture_creation()

    if success:
        print("\n🎉 All tests passed! Lecture creation should work.")
        print("\n🔧 If lectures still not working in your app:")
        print("1. Check API permissions (IsAuthenticated, IsEnrolled)")
        print("2. Verify file upload configuration")
        print("3. Check CORS settings for frontend")
        print("4. Review server logs for detailed errors")
    else:
        print("\n❌ Tests failed. Check the errors above.")

if __name__ == '__main__':
    main()
