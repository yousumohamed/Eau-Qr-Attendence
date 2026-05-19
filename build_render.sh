#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Create superuser (|| true prevents the script from crashing if the user already exists)
DJANGO_SUPERUSER_USERNAME=sadiq \
DJANGO_SUPERUSER_EMAIL=sadiq@gmail.com \
DJANGO_SUPERUSER_PASSWORD=sadiq123 \
python manage.py createsuperuser --noinput || true
