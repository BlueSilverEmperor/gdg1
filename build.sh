#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install production dependencies
pip install -r requirements.txt

# Collect static files for WhiteNoise
python manage.py collectstatic --noinput

# Apply database migrations to PostgreSQL
python manage.py migrate

# Auto-seed initial 100 realistic campus listings if the database is currently empty
python manage.py shell -c "from marketplace.models import Listing; from django.core.management import call_command; call_command('seed_data') if Listing.objects.count() == 0 else print('Listings present: %d' % Listing.objects.count())"
