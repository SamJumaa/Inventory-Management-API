"""
Serializers for sales app: Sale and SaleItem.
"""

from django.db import transaction
from rest_framework import serializers

from catalog.models import Product
from catalog.serializers import ProductListSerializer
from inventory.models import Stock, StockMovement
from .models import Sale, SaleItem


class SaleItemSerializer(serializers.ModelSerializer):
    """Serializer for SaleItem."""

    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),  # type: ignore[attr-defined]
        source="product",
        write_only=True,
    )
    line_total = serializers.SerializerMethodField()

    class Meta:
        """Meta options for SaleItemSerializer."""
        model = SaleItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "unit_price",
            "line_total",
        ]
        read_only_fields = ["id", "product", "line_total"]

    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def validate_unit_price(self, value):
        """Validate unit price is not negative."""
        if value < 0:
            raise serializers.ValidationError("Unit price must be greater than or equal to 0.")
        return value

    def get_line_total(self, obj):
        """Return quantity multiplied by unit price."""
        return obj.line_total()


class SaleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for sale list endpoint."""

    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        """Meta options for SaleListSerializer."""
        model = Sale
        fields = [
            "id",
            "customer_name",
            "reference_no",
            "status",
            "total_amount",
            "item_count",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "total_amount",
            "item_count",
            "created_by_name",
            "created_at",
        ]

    def get_item_count(self, obj):
        """Return number of items in the sale."""
        return obj.items.count()


class SaleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for sale detail endpoint."""

    items = SaleItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        """Meta options for SaleDetailSerializer."""
        model = Sale
        fields = [
            "id",
            "created_by_name",
            "customer_name",
            "reference_no",
            "status",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by_name",
            "status",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        ]

    def validate_customer_name(self, value):
        """Validate customer name if provided."""
        if value is not None and not value.strip():
            raise serializers.ValidationError("Customer name cannot be empty.")
        return value.strip() if value else None

    def validate_reference_no(self, value):
        """Validate reference number uniqueness if provided."""
        if value:
            qs = Sale.objects.filter(reference_no=value)
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():  # type: ignore[attr-defined]
                raise serializers.ValidationError("Reference number must be unique.")
        return value


class ConfirmSaleSerializer(serializers.Serializer):
    """Serializer for confirming a sale."""

    def create(self, validated_data):
        raise NotImplementedError("Use save() to confirm sale.")

    def update(self, instance, validated_data):
        raise NotImplementedError("Use save() to confirm sale.")

    def validate(self, data):
        """Validate that the sale can be confirmed."""
        sale = self.context.get("sale")

        if not sale:
            raise serializers.ValidationError("Sale not found.")

        if sale.status != "DRAFT":
            raise serializers.ValidationError(
                f"Only DRAFT sales can be confirmed. Current status: {sale.status}."
            )

        if not sale.items.exists():
            raise serializers.ValidationError("Cannot confirm a sale without items.")

        insufficient_stock = []
        for item in sale.items.select_related("product"):
            stock, _ = Stock.objects.get_or_create(  # type: ignore[attr-defined]
                product=item.product,
                defaults={"quantity": 0},
            )

            if stock.quantity < item.quantity:
                insufficient_stock.append(
                    f"{item.product.sku}: available={stock.quantity}, requested={item.quantity}"
                )

        if insufficient_stock:
            raise serializers.ValidationError(
                f"Insufficient stock: {'; '.join(insufficient_stock)}"
            )

        return data

    def save(self):
        """
        Confirm sale:
        - validate stock
        - decrease stock
        - create OUT stock movements
        - update total_amount
        - mark sale as confirmed
        """
        sale = self.context["sale"]
        user = self.context["request"].user

        with transaction.atomic():
            for item in sale.items.select_related("product"):
                stock, _ = Stock.objects.get_or_create(  # type: ignore[attr-defined]
                    product=item.product,
                    defaults={"quantity": 0},
                )

                stock.quantity -= item.quantity
                stock.save(update_fields=["quantity", "updated_at"])

                StockMovement.objects.create(  # type: ignore[attr-defined]
                    product=item.product,
                    created_by=user,
                    movement_type="OUT",
                    quantity=item.quantity,
                    reference=sale.reference_no or f"SO-{sale.id}",
                    notes=f"Sale {sale.id} to {sale.customer_name or 'Customer'}",
                )

            sale.total_amount = sale.compute_total()
            sale.status = "CONFIRMED"
            sale.save(update_fields=["total_amount", "status", "updated_at"])

        return sale
