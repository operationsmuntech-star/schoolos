web: python manage.py migrate && python manage.py collectstatic --noinput --clear && gunicorn backend.config.wsgi --bind 0.0.0.0:$PORT --workers 2
