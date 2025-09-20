#!/bin/bash

echo "=== Database Initialization ==="

# Ensure we're in the right directory
cd /opt/render/project/src

# Test database connection
echo "Testing database connection..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eld_project.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Check if we should run migrations (only if SKIP_MIGRATIONS is not set)
if [ "$SKIP_MIGRATIONS" != "true" ]; then
    echo "Running Django migrations..."
    python manage.py migrate --verbosity=2

    # Check if migration was successful
    if [ $? -eq 0 ]; then
        echo "✅ Migrations completed successfully"
    else
        echo "❌ Migration failed, trying sync..."
        python manage.py migrate --run-syncdb
    fi
else
    echo "Skipping migrations (SKIP_MIGRATIONS=true)"
fi

# Verify tables exist
echo "Verifying database tables..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eld_project.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public';\")
    tables = [row[0] for row in cursor.fetchall()]
    print(f'Tables: {tables}')
    if 'eld_app_trip' in tables:
        print('✅ eld_app_trip table exists!')
    else:
        print('❌ eld_app_trip table missing!')
"

echo "=== Starting Gunicorn ==="
exec gunicorn eld_project.wsgi:application --bind 0.0.0.0:$PORT