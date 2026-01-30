#!/bin/bash
# Production deployment script for Railway

echo "🔄 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "✅ Static files collected to staticfiles/"
echo "📊 Checking staticfiles directory..."
ls -la staticfiles/ | head -20

echo "✨ Ready for production!"
