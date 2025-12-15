# E-Learning Backend - Udemy Clone

A comprehensive e-learning platform backend built with Django REST Framework, featuring video streaming, payments, user management, and more.

## 🚀 Features

### ✅ Core Features
- **User Management**: Registration, authentication, profiles
- **Course Management**: Create, organize, and manage courses
- **Video Streaming**: HLS adaptive bitrate streaming (1080p, 720p, 480p, 360p)
- **Payment Integration**: Razorpay payment gateway
- **Shopping Cart**: Add to cart, coupons, checkout
- **Progress Tracking**: Video progress and course completion
- **Content Access Control**: Enrollment-based restrictions

### 🎯 Advanced Features
- **Multi-Quality Video**: Automatic transcoding and HLS generation
- **Background Processing**: Async video processing with threading
- **Coupon System**: Discount codes with usage limits
- **Wishlist**: Save courses for later
- **Review System**: Course ratings and reviews
- **Analytics Dashboard**: Instructor and student statistics

## 🛠️ Tech Stack

### Backend
- **Django 5.1.5** - Web framework
- **Django REST Framework 3.14.0** - API framework
- **MySQL** - Database
- **JWT Authentication** - Token-based auth
- **Razorpay** - Payment gateway

### Video Processing
- **FFmpeg** - Video transcoding
- **HLS.js** - Client-side HLS player
- **Multi-quality streaming** - Adaptive bitrate

### Infrastructure
- **Gunicorn** - WSGI server
- **Nginx** - Reverse proxy
- **AWS S3** - File storage (optional)
- **Celery** - Background tasks (optional)

## 📋 Prerequisites

### System Requirements
- **Python 3.8+**
- **MySQL 8.0+**
- **FFmpeg** (for video processing)
- **Git**

### Installing FFmpeg
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

## 🔧 Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd elearning_backend
```

### 2. Run Installation Script
```bash
# Basic installation
./install.sh

# With development dependencies
./install.sh --dev

# With superuser creation
./install.sh --createsuperuser
```

### 3. Manual Installation (Alternative)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Setup environment
cp .env.example .env  # Configure your settings

# Database setup
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DB_NAME=elearning_db
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306

# Razorpay
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXX
RAZORPAY_KEY_SECRET=your-secret-key

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=us-east-1

# Redis/Celery (Optional)
REDIS_URL=redis://localhost:6379/0
```

## 🚀 Running the Application

### Development Server
```bash
# Activate virtual environment
source venv/bin/activate

# Run Django development server
python manage.py runserver

# Server will be available at: http://127.0.0.1:8000
```

### Production Deployment
```bash
# Using Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Using Nginx + Gunicorn (recommended)
# Configure nginx.conf and run:
sudo systemctl start nginx
gunicorn config.wsgi:application --bind unix:/tmp/gunicorn.sock
```

## 📚 API Documentation

### Authentication Endpoints
```
POST /api/users/login/          # User login
POST /api/users/register/       # User registration
POST /api/users/logout/         # User logout
```

### Course Management
```
GET  /api/courses/courses/              # List courses
POST /api/courses/courses/              # Create course (instructor only)
GET  /api/courses/courses/{id}/         # Course details
PUT  /api/courses/courses/{id}/         # Update course
```

### Video & Content
```
GET /api/courses/{course_id}/sections/                      # Course sections
GET /api/courses/{course_id}/sections/{section_id}/lectures/ # Section lectures
GET /api/lectures/{lecture_id}/                             # Lecture details with video URL
```

### Shopping & Payments
```
POST /api/shopping/cart/add/            # Add to cart
GET  /api/shopping/cart/get_cart_summary/ # Cart details
POST /api/payments/single/create/       # Create payment
POST /api/payments/single/verify/       # Verify payment
```

### User Profile
```
GET  /api/users/profile/                # Get profile
PATCH /api/users/profile/               # Update profile
POST /api/users/profile/change-password/ # Change password
GET  /api/users/profile/statistics/     # User statistics
```

## 🎬 Video Processing

### Automatic Video Processing
1. **Upload**: Instructor uploads MP4 video
2. **Processing**: System automatically creates multiple qualities
3. **HLS Generation**: Creates adaptive streaming playlist
4. **Streaming**: Users get single URL with auto quality selection

### Manual Video Processing
```bash
# Process specific lecture
python manage.py process_videos --lecture-id 123

# Process all pending videos
python manage.py process_videos --all
```

### Video Quality Options
- **1080p**: 1920x1080 (5 Mbps) - High quality
- **720p**: 1280x720 (3 Mbps) - HD quality
- **480p**: 854x480 (1.5 Mbps) - Standard quality
- **360p**: 640x360 (1 Mbps) - Mobile quality

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test courses
python manage.py test users

# With coverage
pytest --cov=. --cov-report=html
```

### API Testing
```bash
# Using HTTPie
http POST http://localhost:8000/api/users/register/ email=user@example.com password=pass123

# Using curl
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'
```

## 📁 Project Structure

```
elearning_backend/
├── config/                 # Django settings
├── courses/                # Course management app
│   ├── models.py          # Course, Lecture, Section models
│   ├── views.py           # Course API views
│   ├── serializers.py     # API serializers
│   ├── video_utils.py     # Video processing utilities
│   └── management/commands/ # Custom management commands
├── users/                  # User management app
├── payments/               # Payment integration
├── shopping/               # Cart and checkout
├── core/                   # Core utilities
├── media/                  # User uploaded files
├── static/                 # Static assets
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── install.sh             # Installation script
└── README.md              # This file
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: Student/Instructor/Admin permissions
- **Content Protection**: Enrollment-based access control
- **Payment Security**: Razorpay signature verification
- **CORS Protection**: Configured CORS policies
- **Input Validation**: Comprehensive data validation

## 📊 Monitoring & Logging

### Error Monitoring (Optional)
```python
# Add to settings.py for Sentry integration
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

### Performance Monitoring
- **Django Debug Toolbar**: Development performance monitoring
- **Query Optimization**: Select related and prefetch related usage
- **Caching**: Redis caching for frequently accessed data

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Cloud Deployment
- **AWS**: EC2 + RDS + S3 + CloudFront
- **GCP**: App Engine + Cloud SQL + Cloud Storage
- **Azure**: App Service + Database + Blob Storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

---

## 🎯 Quick Start

```bash
# 1. Install dependencies
./install.sh --dev

# 2. Configure environment
nano .env

# 3. Setup database
python manage.py migrate

# 4. Create admin user
python manage.py createsuperuser

# 5. Start development server
python manage.py runserver

# 6. Access admin panel
# http://127.0.0.1:8000/admin/
```

**Your Udemy-like e-learning platform is now ready! 🚀**