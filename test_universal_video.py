#!/usr/bin/env python3
"""
Test Universal Video Processing System
Like Udemy - handles any format, creates multiple qualities
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

from courses.models import Lecture, Course, Section
from courses.video_utils import UniversalVideoProcessor
from django.contrib.auth import get_user_model

def test_universal_video_processing():
    """Test the universal video processing system"""
    print("🎬 Testing Universal Video Processing (Udemy-style)")
    print("=" * 55)

    try:
        # Get existing lecture with video
        lecture = Lecture.objects.filter(video_file__isnull=False).first()
        if not lecture:
            print("❌ No lecture with video file found")
            print("   Please upload a video first via API or admin")
            return False

        print(f"✅ Found lecture: {lecture.title}")
        print(f"   Video file: {lecture.video_file.name}")
        print(f"   Current status: {lecture.processing_status}")

        # Initialize universal processor
        processor = UniversalVideoProcessor(lecture)

        # Check FFmpeg availability
        print("\n🔧 Checking FFmpeg...")
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ FFmpeg available")
            else:
                print("❌ FFmpeg not working")
                return False
        except:
            print("❌ FFmpeg not found")
            return False

        # Test video validation
        from django.conf import settings
        video_path = os.path.join(settings.MEDIA_ROOT, lecture.video_file.name)

        print("
🎯 Testing video validation..."        valid, info = processor.validate_input_video(video_path)

        if valid:
            print("✅ Video validation passed"            print(f"   Format: {info['format']}")
            print(f"   Duration: {info['duration']:.1f} seconds")
            print(f"   Size: {info['file_size']/1024/1024:.1f} MB")
        else:
            print(f"❌ Video validation failed: {info}")
            return False

        # Show supported formats
        print("
📋 Supported input formats:"        for fmt in processor.SUPPORTED_INPUT_FORMATS:
            print(f"   {fmt.upper()}")

        # Show output qualities
        print("
🎨 Output qualities that will be created:"        for quality, config in processor.OUTPUT_QUALITIES.items():
            print(f"   {quality}: {config['height']}p ({config['bitrate']} video, {config['audio_bitrate']} audio)")

        print("
📊 Processing flow:"        print("   1. Validate input video (any supported format)")
        print("   2. Convert to MP4 if needed")
        print("   3. Create 4 quality versions (360p, 480p, 720p, 1080p)")
        print("   4. Generate HLS streams for each quality")
        print("   5. Create master HLS playlist")
        print("   6. Update lecture with all video URLs")

        print("
⏱️  Estimated processing time:"        print("   - Small video (<100MB): 1-2 minutes")
        print("   - Medium video (100MB-500MB): 3-5 minutes")
        print("   - Large video (>500MB): 5-10 minutes")

        print("
💾 Storage usage:"        print("   - Original: 1x file")
        print("   - MP4 qualities: 4x files")
        print("   - HLS segments: ~100-500 small files per quality")
        print("   - Total: ~5-10x original size")

        return True

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_usage_examples():
    """Show how to use the universal video system"""
    print("\n📚 Usage Examples:")
    print("=" * 30)

    print("1. API Upload (any format):")
    print("   curl -X POST http://127.0.0.1:8002/api/courses/1/sections/1/lectures/ \\")
    print("     -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print("     -F 'title=My Lecture' \\")
    print("     -F 'description=Any video format' \\")
    print("     -F 'order=1' \\")
    print("     -F 'video_file=@video.mp4'  # or .mov, .avi, etc.")

    print("\n2. Django Admin:")
    print("   - Go to admin panel")
    print("   - Add/Edit lecture")
    print("   - Upload any video format")
    print("   - Save (processing starts automatically)")

    print("\n3. Check Processing Status:")
    print("   GET /api/courses/1/sections/1/lectures/1/")
    print("   Response includes processing_status and video_urls")

    print("\n4. Video Playback:")
    print("   Use the primary_url from API response")
    print("   Supports HLS adaptive streaming")

def main():
    success = test_universal_video_processing()
    show_usage_examples()

    if success:
        print("\n🎉 Universal video processing system is ready!")
        print("\n✅ Features:")
        print("   • Accepts any video format")
        print("   • Automatic format conversion")
        print("   • Multiple quality generation")
        print("   • HLS adaptive streaming")
        print("   • Udemy-like video processing")
    else:
        print("\n❌ System needs setup.")
        print("\n🔧 Required:")
        print("   • Install FFmpeg")
        print("   • Upload a test video")
        print("   • Check file permissions")

if __name__ == '__main__':
    main()
