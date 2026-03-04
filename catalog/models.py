"""
Models for catalog app: Category and Product.
"""
from django.db import models
from django.core.validators import MinValueValidator


class Category(models.Model):
    """Category model for organizing products.

    Fields:
    - name: unique category name
    - description: optional description
    - created_at, updated_at: timestamps
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Category name (must be unique)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional category description"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Metadata options for the Category model."""

        ordering = ['name']
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self) -> str:
        return str(self.name)


class Product(models.Model):
    """
    Product model representing inventory items.

    Fields:
    - category: optional FK to Category
    - name: product name
    - sku: unique stock-keeping unit
    - description: optional description
    - unit_price: price per unit (>= 0)
    - reorder_level: minimum stock threshold (>= 0, default 0)
    - is_active: whether product is available (default True)
    - created_at, updated_at: timestamps
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Optional category for this product"
    )
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Product name"
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique stock-keeping unit"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional product description"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price per unit (must be >= 0)"
    )
    reorder_level = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum stock level before reorder (default 0)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether product is available for purchase/sale"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    """Meta options for the product model."""

    class Meta:
        """Metadata options for the product model."""

        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"
