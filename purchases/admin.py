"""
Django admin configuration for purchases app.
"""

from django.contrib import admin
from .models import Purchase, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    """Inline admin for PurchaseItem."""
    model = PurchaseItem
    extra = 1
    fields = ["product", "quantity", "unit_cost"]


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """Admin interface for Purchase model."""

    list_display = [
        "id",
        "supplier_name",
        "reference_no",
        "status",
        "total_cost",
        "created_by",
        "created_at",
    ]

    list_filter = ["status", "created_at", "created_by"]

    search_fields = ["supplier_name", "reference_no"]

    readonly_fields = ["created_at", "updated_at", "total_cost"]

    ordering = ["-created_at"]

    inlines = [PurchaseItemInline]

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("supplier_name", "reference_no", "created_by"),
            },
        ),
        (
            "Status",
            {
                "fields": ("status", "total_cost"),
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
        """Make fields readonly if purchase is confirmed."""
        readonly = list(self.readonly_fields)

        if obj and obj.status == "CONFIRMED":
            readonly.extend(["supplier_name", "reference_no"])

        return readonly
