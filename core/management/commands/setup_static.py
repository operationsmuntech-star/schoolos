"""
Custom management command to ensure static files are properly configured
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from pathlib import Path
from django.conf import settings


class Command(BaseCommand):
    help = 'Ensures static files directory is created and files are collected'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing static files before collection',
        )

    def handle(self, *args, **options):
        staticfiles_dir = Path(settings.STATIC_ROOT)
        
        # Ensure directory exists
        self.stdout.write(f"Creating staticfiles directory at {staticfiles_dir}...")
        try:
            staticfiles_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
            self.stdout.write(self.style.SUCCESS("✓ Directory created/verified"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error creating directory: {e}"))
            return

        # Collect static files
        clear = options.get('clear', False)
        self.stdout.write(f"Collecting static files (clear={clear})...")
        try:
            call_command('collectstatic', verbosity=2, interactive=False, clear=clear)
            self.stdout.write(self.style.SUCCESS("✓ Static files collected successfully"))
            
            # Verify collection
            css_files = list(staticfiles_dir.rglob('*.css'))
            js_files = list(staticfiles_dir.rglob('*.js'))
            
            self.stdout.write(f"  - CSS files: {len(css_files)}")
            self.stdout.write(f"  - JS files: {len(js_files)}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error collecting static files: {e}"))
