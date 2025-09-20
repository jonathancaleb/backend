#!/usr/bin/env bash
# exit on error
set -o errexit

echo "============================================"
echo "Starting build process..."
echo "============================================"

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "============================================"
echo "Current working directory:"
pwd
echo "============================================"

echo "Listing project files:"
ls -la

echo "============================================"
echo "Django version and setup check:"
python -c "import django; print('Django version:', django.get_version())"

echo "============================================"
echo "Running Django checks..."
python manage.py check

echo "============================================"
echo "Making migrations (if needed)..."
python manage.py makemigrations --verbosity=2

echo "============================================"
echo "Showing migration status..."
python manage.py showmigrations

echo "============================================"
echo "Running database migrations..."
python manage.py migrate --verbosity=2

echo "============================================"
echo "Running custom database initialization..."
python manage.py init_db

echo "============================================"
echo "Collecting static files..."
python manage.py collectstatic --no-input --verbosity=2

echo "============================================"
echo "Build completed successfully!"
echo "============================================"