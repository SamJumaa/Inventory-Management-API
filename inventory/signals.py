"""
Signals for inventory app.

Automatically create a Stock record when a Product is created.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from catalog.models import Product
from .models import Stock


@receiver(post_save, sender=Product)
def create_stock_for_product(sender, instance, created, **kwargs):
    """
    Automatically create a Stock record when a Product is created.
    """
    if created:
        Stock.objects.get_or_create(
            product=instance,
            defaults={"quantity": 0}
        )
