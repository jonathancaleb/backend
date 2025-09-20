from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Run migrations and setup database for local development'

    def handle(self, *args, **options):
        self.stdout.write('=== Setting up database ===')
        
        # Make migrations
        self.stdout.write('Making migrations...')
        call_command('makemigrations', verbosity=2)
        
        # Run migrations
        self.stdout.write('Running migrations...')
        call_command('migrate', verbosity=2)
        
        self.stdout.write(self.style.SUCCESS('✅ Database setup complete!'))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Your local database is now set up')
        self.stdout.write('2. Deploy to Render - migrations will run automatically on first deploy')
        self.stdout.write('3. After first successful deploy, set SKIP_MIGRATIONS=true in Render dashboard')