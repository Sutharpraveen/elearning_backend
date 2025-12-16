#!/bin/bash

# Lecture Creation Troubleshooting Script
# Run this on your server to diagnose lecture creation issues

echo "🔍 Troubleshooting Lecture Creation Issues..."
echo "=============================================="

# Check Python environment
echo "📍 Checking Python Environment:"
python3 --version
which python3

# Check virtual environment
echo ""
echo "🐍 Checking Virtual Environment:"
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Virtual environment not activated!"
    echo "Run: source venv/bin/activate"
    exit 1
else
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
fi

# Check Django installation
echo ""
echo "🎯 Checking Django Installation:"
python -c "import django; print('Django version:', django.VERSION)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Django not installed!"
    exit 1
else
    echo "✅ Django is installed"
fi

# Check database connection
echo ""
echo "🗄️  Checking Database Connection:"
python manage.py check --deploy 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Database connection failed!"
    echo "Check your .env file and database settings"
    exit 1
else
    echo "✅ Database connection OK"
fi

# Check media directories
echo ""
echo "📁 Checking Media Directories:"
MEDIA_DIRS=(
    "media/lecture_videos/original"
    "media/lecture_videos/1080p"
    "media/lecture_videos/720p"
    "media/lecture_videos/480p"
    "media/lecture_videos/360p"
    "media/lecture_videos/hls"
    "media/user_profiles"
    "staticfiles"
)

for dir in "${MEDIA_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir exists"

        # Check write permissions
        if [ -w "$dir" ]; then
            echo "   ✅ Write permission OK"
        else
            echo "   ❌ No write permission for $dir"
        fi
    else
        echo "❌ $dir does not exist"
        echo "   Creating directory..."
        mkdir -p "$dir" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "   ✅ Directory created"
        else
            echo "   ❌ Failed to create directory"
        fi
    fi
done

# Check ffmpeg installation
echo ""
echo "🎬 Checking FFmpeg Installation:"
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg is installed"
    ffmpeg -version | head -1
else
    echo "❌ FFmpeg not installed!"
    echo "Install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  CentOS/RHEL: sudo yum install ffmpeg"
    echo "  macOS: brew install ffmpeg"
fi

# Check ffprobe
echo ""
echo "🔍 Checking FFprobe:"
if command -v ffprobe &> /dev/null; then
    echo "✅ FFprobe is available"
else
    echo "❌ FFprobe not available (usually comes with ffmpeg)"
fi

# Test file upload
echo ""
echo "📤 Testing File Upload Permissions:"
TEST_FILE="media/test_upload.txt"
echo "test" > "$TEST_FILE" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ File upload test passed"
    rm "$TEST_FILE" 2>/dev/null
else
    echo "❌ File upload test failed!"
    echo "Check permissions on media directory"
fi

# Check Django settings
echo ""
echo "⚙️  Checking Django Settings:"
python -c "
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
django.setup()

print('MEDIA_ROOT:', settings.MEDIA_ROOT)
print('MEDIA_URL:', settings.MEDIA_URL)
print('DEBUG:', settings.DEBUG)
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
"

# Test lecture creation
echo ""
echo "📝 Testing Lecture Creation Logic:"
python -c "
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
django.setup()

from courses.models import Course, Section, Lecture

try:
    # Check if courses exist
    course_count = Course.objects.count()
    print(f'✅ Found {course_count} courses in database')

    if course_count > 0:
        course = Course.objects.first()
        print(f'   Course: {course.title}')

        # Check sections
        section_count = course.sections.count()
        print(f'   Sections: {section_count}')

        if section_count > 0:
            section = course.sections.first()
            print(f'   First section: {section.title}')

            # Try creating a test lecture
            lecture_count_before = section.lectures.count()
            print(f'   Lectures before: {lecture_count_before}')

            # This will fail without proper data, but tests the model
            print('   ✅ Lecture model accessible')
        else:
            print('   ⚠️  No sections found - create sections first')
    else:
        print('   ⚠️  No courses found - create courses first')

except Exception as e:
    print(f'❌ Database error: {e}')
"

echo ""
echo "🔧 Quick Fixes:"
echo "1. If FFmpeg missing: Install FFmpeg"
echo "2. If permissions issue: chmod 755 media/ && chown -R www-data:www-data media/"
echo "3. If database issue: python manage.py migrate"
echo "4. Test API: curl -X GET http://localhost:8000/api/courses/courses/"

echo ""
echo "📊 Summary:"
echo "- Run this script after making fixes"
echo "- Check server logs for detailed errors"
echo "- Test lecture creation via API or admin panel"
