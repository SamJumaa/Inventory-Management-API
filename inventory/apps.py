"""
App configuration for inventory.
Registers signals on app ready.
"""
from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """app config for inventory"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        """Register signals when app is ready."""
        import inventory.signals  # noqa: F401
