#!/bin/bash

# Deployment script for eLearning Backend
echo "🚀 Starting deployment..."

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create media directory if it doesn't exist
mkdir -p media

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 755 staticfiles/
chmod 755 media/

# Restart Gunicorn (if running as service)
echo "🔄 Restarting Gunicorn..."
sudo systemctl restart gunicorn || echo "Gunicorn service not found, starting manually..."

# Restart Nginx
echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx

echo "✅ Deployment completed successfully!"
echo "🌐 Your application should be running at: http://yourdomain.com"
echo "📊 Check logs at: logs/django.log"


