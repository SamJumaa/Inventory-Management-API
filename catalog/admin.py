"""
Django admin configuration for catalog app.
"""
from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    list_display = ['name', 'product_count', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    def product_count(self, obj):
        """Display count of products in category."""
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for Product model."""
    list_display = ['sku', 'name', 'category', 'unit_price', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'sku', 'category'),
        }),
        ('Pricing & Inventory', {
            'fields': ('unit_price', 'reorder_level'),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
        ('Description', {
            'fields': ('description',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
