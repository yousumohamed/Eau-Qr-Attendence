#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations only if DATABASE_URL is present
if [ -n "$DATABASE_URL" ]; then
    python manage.py migrate --noinput
fi
