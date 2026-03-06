"""
Models for sales app: Sale and SaleItem.
"""

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Product


class Sale(models.Model):
    """Sale model representing sales orders."""

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("CONFIRMED", "Confirmed"),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="sales",
        help_text="User who created this sale",
    )
    customer_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Optional customer name",
    )
    reference_no = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Optional unique reference (SO number)",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
        db_index=True,
        help_text="Sale status: DRAFT or CONFIRMED",
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total amount computed from items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["reference_no"]),
            models.Index(fields=["created_by", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"SO {self.id} ({self.customer_name or 'No Customer'}) - {self.status}"

    def compute_total(self):
        """Compute total amount from items."""
        return sum(item.quantity * item.unit_price for item in self.items.all())

    def update_total(self):
        """Update total_amount field from items."""
        self.total_amount = self.compute_total()
        self.save(update_fields=["total_amount", "updated_at"])


class SaleItem(models.Model):
    """Sale line item."""

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Sale order this item belongs to",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="sale_items",
        help_text="Product being sold",
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantity sold (must be > 0)",
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price per unit (>= 0)",
    )

    class Meta:
        unique_together = ["sale", "product"]
        indexes = [
            models.Index(fields=["sale"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.sku} x {self.quantity} @ {self.unit_price}"

    def line_total(self):
        """Return quantity * unit_price."""
        return self.quantity * self.unit_price
