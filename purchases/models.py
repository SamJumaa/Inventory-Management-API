"""
Models for purchases app: Purchase and PurchaseItem.
"""

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Product


class Purchase(models.Model):
    """Purchase model representing purchase orders."""

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("CONFIRMED", "Confirmed"),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="purchases",
        help_text="User who created this purchase",
    )
    supplier_name = models.CharField(
        max_length=255,
        help_text="Name of the supplier",
    )
    reference_no = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Optional unique reference (e.g. PO number)",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
        db_index=True,
        help_text="Purchase status: DRAFT or CONFIRMED",
    )
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total cost computed from items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for Purchase model."""

        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["reference_no"]),
            models.Index(fields=["created_by", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"PO {self.id} ({self.supplier_name}) - {self.status}"

    def compute_total(self):
        """Compute total cost from items."""
        return sum(item.quantity * item.unit_cost for item in self.items.all())

    def update_total(self):
        """Update total_cost field from items."""
        self.total_cost = self.compute_total()
        self.save(update_fields=["total_cost", "updated_at"])


class PurchaseItem(models.Model):
    """Purchase line item."""

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Purchase this item belongs to",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="purchase_items",
        help_text="Product being purchased",
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantity ordered (must be > 0)",
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Cost per unit (must be >= 0)",
    )

    class Meta:
        """Meta options for PurchaseItem model."""

        unique_together = ["purchase", "product"]
        indexes = [
            models.Index(fields=["purchase"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.sku} x {self.quantity} @ {self.unit_cost}"

    def line_total(self):
        """Return quantity multiplied by unit cost."""
        return self.quantity * self.unit_cost
