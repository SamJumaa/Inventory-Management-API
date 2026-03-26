"""
Models for inventory app: Stock and StockMovement (Multi-tenant ready).
"""

from __future__ import annotations

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Product
from companies.models import Company


class Stock(models.Model):
    """
    Stock model: one-to-one relationship with Product per company.
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="stocks",
    )

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="stock",
    )

    quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Stock"
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["quantity"]),
        ]

    def __str__(self) -> str:
        return f"{self.company.name} - {self.product} ({self.quantity})"

    def is_low_stock(self) -> bool:
        return self.quantity < self.product.reorder_level


class StockMovement(models.Model):
    """
    Immutable audit log for stock changes.
    """

    MOVEMENT_TYPES = [
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("ADJUSTMENT", "Adjustment"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)

    quantity = models.IntegerField(validators=[MinValueValidator(1)])

    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
    )

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["product", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.product} {self.movement_type} {self.quantity}"
