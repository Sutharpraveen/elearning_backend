#!/bin/bash

# E-Learning Backend Deployment Script for Server
# Run this on your online server

echo "🚀 Deploying E-Learning Backend to Server..."

# Check Python version
python3 --version

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install ffmpeg if available
echo "🎬 Checking for ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg found"
else
    echo "⚠️  ffmpeg not found - video processing will be limited"
fi

# Create media directories
echo "📁 Creating media directories..."
mkdir -p media/lecture_videos/{original,1080p,720p,480p,360p,hls}
mkdir -p media/user_profiles
mkdir -p staticfiles

# Setup database
echo "🗄️  Setting up database..."
python manage.py makemigrations
python manage.py migrate

# Create superuser
echo "👤 Creating superuser..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell

# Collect static files
echo "📄 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Deployment completed!"
echo ""
echo "🎯 To run the server:"
echo "source venv/bin/activate"
echo "python manage.py runserver 0.0.0.0:8000"
echo ""
echo "🌐 Access your app at: http://your-server-ip:8000"
echo "🔧 Admin panel at: http://your-server-ip:8000/admin/"
echo "   Username: admin"
echo "   Password: admin123"

