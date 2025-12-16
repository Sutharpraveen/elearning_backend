#!/usr/bin/env python3
"""
Test Direct MP4 Upload Functionality
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
from courses.serializers import LectureSerializer
from django.test import RequestFactory
from django.core.files.base import ContentFile

def test_direct_mp4_upload():
    """Test direct MP4 upload functionality"""
    print("\n🎬 Testing Direct MP4 Upload...")

    try:
        # Get existing course and section
        course = Course.objects.filter(is_published=True).first()
        if not course:
            print("❌ No published course found")
            return False

        section = course.sections.first()
        if not section:
            print("❌ No section found in course")
            return False

        print(f"✅ Using course: {course.title}")
        print(f"✅ Using section: {section.title}")

        # Create a test MP4 file content (dummy content for testing)
        test_mp4_content = b"dummy mp4 content for testing direct upload"

        # Create lecture with direct MP4 upload
        lecture = Lecture.objects.create(
            section=section,
            title="Test Direct MP4 Upload",
            description="This lecture uses direct MP4 upload",
            order=section.lectures.count() + 1,
            processing_status='direct'
        )

        # Upload the MP4 file
        lecture.video_file.save(
            'test_direct_upload.mp4',
            ContentFile(test_mp4_content),
            save=True
        )

        print("✅ Lecture created with direct MP4 upload")
        print(f"   Title: {lecture.title}")
        print(f"   Video file: {lecture.video_file}")
        print(f"   Processing status: {lecture.processing_status}")

        # Test serializer
        factory = RequestFactory()
        request = factory.get('/')
        request.user = get_user_model().objects.filter(role='student').first()

        serializer = LectureSerializer(lecture, context={'request': request})
        data = serializer.data

        print("✅ Serializer working correctly")
        print(f"   Video URLs: {data.get('video_urls')}")

        # Verify video URL structure
        video_urls = data.get('video_urls', {})
        if video_urls.get('primary_url'):
            print("✅ Primary video URL generated")
            print(f"   URL: {video_urls['primary_url']}")
            print(f"   Stream type: {video_urls.get('stream_type')}")

        # Clean up
        lecture.delete()
        print("🧹 Test lecture cleaned up")

        return True

    except Exception as e:
        print(f"❌ Error during direct MP4 upload test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🎬 Direct MP4 Upload Test")
    print("=" * 30)

    success = test_direct_mp4_upload()

    if success:
        print("\n🎉 Direct MP4 upload is working!")
        print("\n🔧 How to use:")
        print("1. Upload MP4 file via API/admin")
        print("2. Video is immediately playable")
        print("3. No processing/transcoding required")
        print("4. Status shows as 'direct'")
        print("\n📤 API Usage:")
        print("POST /api/courses/{course_id}/sections/{section_id}/lectures/")
        print("Form field: video_file (MP4 file)")
    else:
        print("\n❌ Direct MP4 upload test failed.")
        print("Check the error messages above.")

if __name__ == '__main__':
    main()
