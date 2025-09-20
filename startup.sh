#!/bin/bash

echo "=== Database Initialization ==="

# Ensure we're in the right directory
cd /opt/render/project/src

# Run migrations with error handling
echo "Running Django migrations..."
python manage.py migrate --verbosity=2

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed, trying sync..."
    python manage.py migrate --run-syncdb
fi

# Verify tables exist
echo "Verifying database tables..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eld_project.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
    tables = [row[0] for row in cursor.fetchall()]
    print(f'Tables: {tables}')
    if 'eld_app_trip' in tables:
        print('✅ eld_app_trip table exists!')
    else:
        print('❌ eld_app_trip table missing!')
"

echo "=== Starting Gunicorn ==="
exec gunicorn eld_project.wsgi:application --bind 0.0.0.0:$PORT