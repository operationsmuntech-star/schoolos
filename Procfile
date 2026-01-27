release: python manage.py migrate && python manage.py collectstatic --noinput --verbosity=2
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers=2 --worker-class=sync
