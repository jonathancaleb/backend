from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Initialize database with migrations'

    def handle(self, *args, **options):
        self.stdout.write('Checking database connection...')
        
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS('Database connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database connection failed: {e}'))
            return

        self.stdout.write('Running migrations...')
        try:
            call_command('migrate', verbosity=2)
            self.stdout.write(self.style.SUCCESS('Migrations completed successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Migration failed: {e}'))

        # Verify tables were created
        self.stdout.write('Verifying tables...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f'Tables found: {tables}')
                
                if 'eld_app_trip' in tables:
                    self.stdout.write(self.style.SUCCESS('eld_app_trip table exists!'))
                else:
                    self.stdout.write(self.style.ERROR('eld_app_trip table not found!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Table verification failed: {e}'))