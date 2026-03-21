"""Django app configuration for the accounts app"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the accounts app"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        """Import signals to ensure they are registered"""
        import accounts.signals
