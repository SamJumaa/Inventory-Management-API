"""
Django admin configuration for inventory app.
"""

from django.contrib import admin
from .models import Stock, StockMovement


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    """Admin interface for Stock model."""

    list_display = ["product", "quantity", "reorder_level", "is_low_stock", "updated_at"]
    search_fields = ["product__name", "product__sku"]
    readonly_fields = ["product", "updated_at"]

    def reorder_level(self, obj):
        """Display product reorder level."""
        return obj.product.reorder_level
    reorder_level.short_description = "Reorder Level"

    def is_low_stock(self, obj):
        """Display if stock is below reorder level."""
        return obj.is_low_stock()
    is_low_stock.short_description = "Low Stock"
    is_low_stock.boolean = True


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Admin interface for StockMovement model."""

    list_display = [
        "product",
        "movement_type",
        "quantity",
        "reference",
        "created_by",
        "created_at",
    ]

    list_filter = ["movement_type", "created_at", "product__category"]
    search_fields = ["product__name", "product__sku", "reference", "notes"]

    readonly_fields = [
        "product",
        "movement_type",
        "quantity",
        "created_at",
        "created_by",
    ]

    ordering = ["-created_at"]

    fieldsets = (
        ("Movement Info", {
            "fields": ("product", "movement_type", "quantity"),
        }),
        ("Reference & Notes", {
            "fields": ("reference", "notes"),
        }),
        ("Audit", {
            "fields": ("created_by", "created_at"),
            "classes": ("collapse",),
        }),
    )
