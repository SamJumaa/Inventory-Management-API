"""
Serializers for inventory app: Stock and StockMovement.
"""

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from catalog.models import Product
from catalog.serializers import ProductListSerializer
from .models import Stock, StockMovement


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for User (used in stock movements)."""

    class Meta:
        """Meta options for UserBasicSerializer."""

        model = User
        fields = ["id", "username", "first_name", "last_name"]
        read_only_fields = ["id", "username", "first_name", "last_name"]


class StockMovementSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for StockMovement.
    This acts as an audit log of all stock changes.
    """

    product = ProductListSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    movement_type_display = serializers.CharField(
        source="get_movement_type_display", read_only=True
    )

    class Meta:
        """Meta options for StockMovementSerializer."""

        model = StockMovement
        fields = [
            "id",
            "product",
            "created_by",
            "movement_type",
            "movement_type_display",
            "quantity",
            "reference",
            "notes",
            "created_at",
        ]
        read_only_fields = fields


class StockSerializer(serializers.ModelSerializer):
    """
    Serializer for Stock including product details.
    """

    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    reorder_level = serializers.IntegerField(
        source="product.reorder_level", read_only=True
    )
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        """Meta options for StockSerializer."""

        model = Stock
        fields = [
            "product_id",
            "sku",
            "product",
            "quantity",
            "reorder_level",
            "is_low_stock",
            "updated_at",
        ]
        read_only_fields = fields

    def get_is_low_stock(self, obj):
        """Return True if stock is below reorder level."""
        return obj.is_low_stock()


class AdjustStockSerializer(serializers.Serializer):
    """
    Serializer used to adjust stock levels.

    quantity can be:
    + positive → add stock
    + negative → remove stock

    This will:
    - prevent negative stock
    - create StockMovement
    - update Stock atomically
    """

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def create(self, validated_data):
        """Required by DRF but not used."""
        raise NotImplementedError("Use save() for stock adjustment.")

    def update(self, instance, validated_data):
        """Required by DRF but not used."""
        raise NotImplementedError("Use save() for stock adjustment.")

    def validate_product_id(self, value):
        """Check product exists."""
        if not Product.objects.filter(id=value).exists():  # type: ignore
            raise serializers.ValidationError(
                f"Product with id {value} does not exist."
            )
        return value

    def validate_quantity(self, value):
        """Quantity cannot be zero."""
        if value == 0:
            raise serializers.ValidationError("Quantity cannot be zero.")
        return value

    def validate(self, data):
        """Ensure adjustment won't make stock negative."""
        product = Product.objects.get(id=data["product_id"])  # type: ignore
        stock, _ = Stock.objects.get_or_create(  # type: ignore
            product=product,
            defaults={"quantity": 0},
        )

        new_quantity = stock.quantity + data["quantity"]

        if new_quantity < 0:
            raise serializers.ValidationError(
                {
                    "quantity": (
                        f"Not enough stock. Current: {stock.quantity}, "
                        f"Adjustment: {data['quantity']}, Result: {new_quantity}"
                    )
                }
            )

        return data

    def save(self, user=None):
        """Perform stock adjustment and create stock movement."""
        request = self.context.get("request")
        company = request.user.profile.company

        product = Product.objects.get(id=self.validated_data["product_id"])

        stock, _ = Stock.objects.get_or_create(
            product=product,
            company=company,
            defaults={"quantity": 0, "created_by": user},
        )

        qty = self.validated_data["quantity"]
        notes = self.validated_data.get("notes", "").strip()

        movement_type = "IN" if qty > 0 else "OUT"
        move_qty = abs(qty)

        with transaction.atomic():

            StockMovement.objects.create(
                company=company,
                product=product,
                created_by=user,
                movement_type=movement_type,
                quantity=move_qty,
                notes=f"[ADJUSTMENT] {notes}" if notes else "[ADJUSTMENT]",
            )

            stock.quantity = stock.quantity + qty
            stock.save(update_fields=["quantity", "updated_at"])

        return stock
