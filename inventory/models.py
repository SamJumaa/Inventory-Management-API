"""
Models for inventory app: Stock and StockMovement.

Core principles:
- Stock.quantity must never go negative
- StockMovement is an immutable audit log
- Every stock change creates a movement record
"""

from __future__ import annotations

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Product


class Stock(models.Model):
    """
    Stock model: one-to-one relationship with Product.
    Tracks current quantity for each product.
    """

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="stock",
        help_text="One-to-one relationship with Product",
    )
    quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current stock quantity (must be >= 0)",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for Stock model."""

        verbose_name_plural = "Stock"
        indexes = [
            models.Index(fields=["quantity"]),
        ]

    def __str__(self) -> str:
        return f"Stock({self.product.sku}): {self.quantity}"  # type: ignore[attr-defined]

    def is_low_stock(self) -> bool:
        """Check if stock is below product's reorder level."""
        return self.quantity < self.product.reorder_level  # type: ignore[attr-defined]


class StockMovement(models.Model):
    """
    StockMovement model: immutable audit log of all stock changes.
    """

    MOVEMENT_TYPES = [
        ("IN", "Stock In (Purchase/Receive)"),
        ("OUT", "Stock Out (Sale/Transfer)"),
        ("ADJUSTMENT", "Inventory Adjustment"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_movements",
        help_text="Product affected by this movement",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        help_text="User who created this movement",
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
        help_text="Type of stock movement",
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantity moved (must be positive)",
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Optional reference (PO/SO/etc)",
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional notes about this movement",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for StockMovement model."""

        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "-created_at"]),
            models.Index(fields=["movement_type", "-created_at"]),
            models.Index(fields=["reference"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.product.sku} {self.movement_type} {self.quantity} on {self.created_at}"
        )  # type: ignore[attr-defined]
