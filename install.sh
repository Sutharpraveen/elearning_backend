#!/bin/bash

# E-Learning Backend Installation Script
# Installs all required dependencies and sets up the environment

echo "🚀 Installing E-Learning Backend Dependencies..."

# Check if Python 3.8+ is available
python3 --version || {
    echo "❌ Python 3.8+ is required but not found."
    exit 1
}

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install production dependencies
echo "📚 Installing production dependencies..."
pip install -r requirements.txt

# Install development dependencies (optional)
if [ "$1" = "--dev" ]; then
    echo "🛠️  Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Install ffmpeg system dependency (required for video processing)
echo "🎬 Checking for ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg not found. Installing ffmpeg is recommended for video processing."
    echo "   Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "   macOS: brew install ffmpeg"
    echo "   CentOS/RHEL: sudo yum install ffmpeg"
fi

# Create necessary directories
echo "📁 Creating media directories..."
mkdir -p media/lecture_videos/{original,1080p,720p,480p,360p,hls}
mkdir -p media/user_profiles
mkdir -p staticfiles

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📋 Creating .env template..."
    cat > .env << EOF
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=elearning_db
DB_USER=root
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=3306

# Razorpay Configuration
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# Email Configuration (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# AWS S3 Configuration (Optional - for production)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Redis Configuration (for Celery - Optional)
REDIS_URL=redis://localhost:6379/0
EOF
    echo "⚠️  Please update .env file with your actual configuration values."
fi

# Run database migrations
echo "🗄️  Setting up database..."
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
if [ "$1" = "--createsuperuser" ]; then
    echo "👤 Creating superuser..."
    python manage.py createsuperuser
fi

echo "✅ Installation completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Run: python manage.py runserver"
echo "3. For video processing, ensure ffmpeg is installed"
echo ""
echo "🎯 Your E-Learning platform is ready!"

