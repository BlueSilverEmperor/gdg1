#!/usr/bin/env bash
# Build script for Vercel deployment
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt || python -m pip install -r requirements.txt

echo "Collecting static assets..."
python3 manage.py collectstatic --noinput --clear || python manage.py collectstatic --noinput --clear

echo "Vercel build complete!"
