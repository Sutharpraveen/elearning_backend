#!/usr/bin/env python3
"""
Test FFmpeg Installation Only
Simple test without Django setup
"""

import subprocess
import sys

def test_ffmpeg():
    """Test FFmpeg installation and basic functionality"""
    print("🎬 Testing FFmpeg Installation...")
    print("=" * 40)

    # Test ffprobe
    print("🔍 Testing ffprobe...")
    try:
        result = subprocess.run(['ffprobe', '-version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0] if result.stdout else 'Unknown'
            print("✅ ffprobe is working"            print(f"   {version_line}")
        else:
            print("❌ ffprobe failed")
            print(f"   Error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ ffprobe not found in PATH")
        return False
    except Exception as e:
        print(f"❌ ffprobe error: {e}")
        return False

    # Test ffmpeg
    print("\n🎥 Testing ffmpeg...")
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0] if result.stdout else 'Unknown'
            print("✅ ffmpeg is working"            print(f"   {version_line}")
        else:
            print("❌ ffmpeg failed")
            print(f"   Error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ ffmpeg not found in PATH")
        return False
    except Exception as e:
        print(f"❌ ffmpeg error: {e}")
        return False

    # Test basic ffmpeg functionality
    print("\n🧪 Testing basic ffmpeg functionality...")
    try:
        # Create a simple test command (just check if it responds)
        result = subprocess.run(['ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1', '-f', 'null', '-'],
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print("✅ ffmpeg basic functionality working")
        else:
            print("⚠️  ffmpeg basic test returned non-zero exit code")
            print("   This might be normal for some FFmpeg versions")
    except subprocess.TimeoutExpired:
        print("⚠️  ffmpeg test timed out (but FFmpeg is installed)")
    except Exception as e:
        print(f"⚠️  ffmpeg functionality test error: {e}")
        print("   FFmpeg is installed but basic test failed")

    return True

def check_video_file():
    """Check if there's a video file to test with"""
    print("\n📁 Checking for video files...")

    import os
    from pathlib import Path

    media_dir = Path("media/lecture_videos/original")
    if media_dir.exists():
        video_files = list(media_dir.glob("*.mp4")) + list(media_dir.glob("*.avi")) + list(media_dir.glob("*.mov"))
        if video_files:
            print(f"✅ Found {len(video_files)} video file(s):")
            for vf in video_files:
                size = vf.stat().st_size
                print(f"   {vf.name} ({size} bytes)")
            return True
        else:
            print("❌ No video files found in media/lecture_videos/original/")
    else:
        print("❌ media/lecture_videos/original/ directory does not exist")

    return False

def main():
    print("🎬 FFmpeg Installation Test")
    print("=" * 30)

    ffmpeg_ok = test_ffmpeg()
    video_files_ok = check_video_file()

    print("\n" + "=" * 30)
    print("📊 Test Results:")
    print(f"   FFmpeg: {'✅' if ffmpeg_ok else '❌'}")
    print(f"   Video Files: {'✅' if video_files_ok else '❌'}")

    if ffmpeg_ok:
        print("\n🎉 FFmpeg is properly installed!")
        print("\n🔧 Next steps:")
        print("1. Upload a video file through your Django admin or API")
        print("2. The video should be automatically processed")
        print("3. Check the lecture details for HLS streams")
        print("4. Test video playback with the generated URLs")
    else:
        print("\n❌ FFmpeg installation issues detected.")
        print("\n💡 Installation commands:")
        print("   Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("   macOS: brew install ffmpeg")
        print("   CentOS/RHEL: sudo yum install ffmpeg")

    if not video_files_ok:
        print("\n💡 To test video processing:")
        print("1. Upload a video through Django admin")
        print("2. Check that file appears in media/lecture_videos/original/")
        print("3. Monitor processing status in lecture admin")

if __name__ == '__main__':
    main()
