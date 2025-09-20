#!/usr/bin/env python
"""
Startup script to ensure database is properly initialized
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eld_project.settings')
    django.setup()
    
    print("=== Database Initialization ===")
    
    # Run migrations
    print("Running migrations...")
    execute_from_command_line(['manage.py', 'migrate', '--verbosity=2'])
    
    # Verify tables exist
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables in database: {tables}")
        
        if 'eld_app_trip' in tables:
            print("✅ eld_app_trip table exists!")
        else:
            print("❌ eld_app_trip table missing!")
            # Force create tables
            execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
    
    print("=== Starting application ===")
    # Start gunicorn with proper port
    port = os.environ.get('PORT', '8000')
    os.system(f'gunicorn eld_project.wsgi:application --bind 0.0.0.0:{port}')