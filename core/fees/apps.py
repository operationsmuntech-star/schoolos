from django.apps import AppConfig

class FeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.fees'
    verbose_name = 'Fees Management'

    def ready(self):
        """Connect signals when app is ready"""
        from . import signals
        signals.connect_signals()
