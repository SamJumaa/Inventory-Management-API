"""
Django admin configuration for sales app.
"""

from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    """Inline admin for SaleItem."""
    model = SaleItem
    extra = 1
    fields = ["product", "quantity", "unit_price"]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """Admin interface for Sale model."""

    list_display = [
        "id",
        "customer_name",
        "reference_no",
        "status",
        "total_amount",
        "created_by",
        "created_at",
    ]

    list_filter = ["status", "created_at", "created_by"]

    search_fields = ["customer_name", "reference_no"]

    readonly_fields = ["created_at", "updated_at", "total_amount"]

    ordering = ["-created_at"]

    inlines = [SaleItemInline]

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("customer_name", "reference_no", "created_by"),
            },
        ),
        (
            "Status",
            {
                "fields": ("status", "total_amount"),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly if sale is confirmed."""
        readonly = list(self.readonly_fields)

        if obj and obj.status == "CONFIRMED":
            readonly.extend(["customer_name", "reference_no"])

        return readonly
