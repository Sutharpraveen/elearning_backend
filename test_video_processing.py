#!/usr/bin/env python3
"""
Test Video Processing Functionality
Run this to diagnose video processing issues
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

from courses.models import Lecture
from courses.video_utils import VideoProcessor
import subprocess

def test_ffmpeg():
    """Test if FFmpeg is available and working"""
    print("🎬 Testing FFmpeg Installation...")

    try:
        # Test ffprobe
        result = subprocess.run(['ffprobe', '-version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFprobe is working")
            print(f"   Version: {result.stdout.split()[2] if len(result.stdout.split()) > 2 else 'Unknown'}")
        else:
            print("❌ FFprobe failed")
            return False

        # Test ffmpeg
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg is working")
            print(f"   Version: {result.stdout.split()[2] if len(result.stdout.split()) > 2 else 'Unknown'}")
        else:
            print("❌ FFmpeg failed")
            return False

        return True

    except FileNotFoundError:
        print("❌ FFmpeg/FFprobe not found in PATH")
        print("   Install FFmpeg: sudo apt-get install ffmpeg")
        return False
    except Exception as e:
        print(f"❌ FFmpeg test error: {e}")
        return False

def test_video_processing():
    """Test video processing functionality"""
    print("\n🎥 Testing Video Processing...")

    try:
        # Get a lecture with video
        lecture = Lecture.objects.filter(original_video__isnull=False).first()

        if not lecture:
            print("❌ No lecture with video found")
            print("   Upload a video to a lecture first")
            return False

        print(f"✅ Found lecture: {lecture.title}")
        print(f"   Video file: {lecture.original_video.name}")
        print(f"   Processing status: {lecture.processing_status}")

        # Check if original video file exists
        media_root = django.conf.settings.MEDIA_ROOT
        video_path = os.path.join(media_root, lecture.original_video.name)

        if os.path.exists(video_path):
            print("✅ Original video file exists")
            print(f"   Path: {video_path}")
            print(f"   Size: {os.path.getsize(video_path)} bytes")
        else:
            print("❌ Original video file does NOT exist")
            print(f"   Expected path: {video_path}")
            return False

        # Test video info extraction
        processor = VideoProcessor(lecture)
        duration, file_size = processor.get_video_info(video_path)

        if duration > 0:
            print("✅ Video info extraction working")
            print(f"   Duration: {duration} seconds")
            print(f"   File size: {file_size} bytes")
        else:
            print("❌ Video info extraction failed")
            return False

        # Test HLS directory creation
        hls_dir = os.path.join(media_root, 'lecture_videos', 'hls')
        if os.path.exists(hls_dir):
            print("✅ HLS directory exists")
        else:
            print("❌ HLS directory does not exist")
            print("   Creating HLS directory...")
            os.makedirs(hls_dir, exist_ok=True)
            print("   ✅ HLS directory created")

        return True

    except Exception as e:
        print(f"❌ Video processing test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_serving():
    """Test if media files are being served correctly"""
    print("\n🌐 Testing File Serving...")

    try:
        from django.conf import settings
        print(f"✅ MEDIA_ROOT: {settings.MEDIA_ROOT}")
        print(f"✅ MEDIA_URL: {settings.MEDIA_URL}")
        print(f"✅ DEBUG: {settings.DEBUG}")

        # Check if media URL is configured in URLs
        with open('config/urls.py', 'r') as f:
            urls_content = f.read()

        if 'static(settings.MEDIA_URL' in urls_content:
            print("✅ Media URL configured in urls.py")
        else:
            print("❌ Media URL NOT configured in urls.py")

        return True

    except Exception as e:
        print(f"❌ File serving test error: {e}")
        return False

def main():
    print("🎬 E-Learning Video Processing Test")
    print("=" * 40)

    # Test FFmpeg
    ffmpeg_ok = test_ffmpeg()

    # Test video processing
    processing_ok = test_video_processing()

    # Test file serving
    serving_ok = test_file_serving()

    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"   FFmpeg: {'✅' if ffmpeg_ok else '❌'}")
    print(f"   Video Processing: {'✅' if processing_ok else '❌'}")
    print(f"   File Serving: {'✅' if serving_ok else '❌'}")

    if ffmpeg_ok and processing_ok and serving_ok:
        print("\n🎉 All video processing tests passed!")
        print("\n🔧 If videos still not working:")
        print("1. Upload a video through the API/admin")
        print("2. Wait for processing to complete")
        print("3. Check the lecture API response for video_urls")
        print("4. Test HLS streams with a video player")
    else:
        print("\n❌ Some tests failed. Fix the issues above.")

        if not ffmpeg_ok:
            print("\n💡 FFmpeg Installation:")
            print("   Ubuntu/Debian: sudo apt-get install ffmpeg")
            print("   macOS: brew install ffmpeg")
            print("   CentOS/RHEL: sudo yum install ffmpeg")

        if not processing_ok:
            print("\n💡 Video Processing Issues:")
            print("   1. Check file permissions on media/ directory")
            print("   2. Verify video file format (MP4 recommended)")
            print("   3. Check Django logs for processing errors")

        if not serving_ok:
            print("\n💡 File Serving Issues:")
            print("   1. Add media URL config to urls.py")
            print("   2. Check web server configuration")
            print("   3. Verify file permissions")

if __name__ == '__main__':
    main()
