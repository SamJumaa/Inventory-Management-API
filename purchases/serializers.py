"""
Serializers for purchases app: Purchase and PurchaseItem.
"""

from django.db import transaction
from rest_framework import serializers

from catalog.models import Product
from catalog.serializers import ProductListSerializer
from inventory.models import Stock, StockMovement
from .models import Purchase, PurchaseItem


class PurchaseItemSerializer(serializers.ModelSerializer):
    """Serializer for PurchaseItem."""

    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),  # type: ignore[attr-defined]
        source="product",
        write_only=True,
    )
    line_total = serializers.SerializerMethodField()

    class Meta:
        """Meta options for PurchaseItemSerializer."""
        model = PurchaseItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "unit_cost",
            "line_total",
        ]
        read_only_fields = ["id", "product", "line_total"]

    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def validate_unit_cost(self, value):
        """Validate unit cost is not negative."""
        if value < 0:
            raise serializers.ValidationError("Unit cost must be greater than or equal to 0.")
        return value

    def get_line_total(self, obj):
        """Return quantity multiplied by unit cost."""
        return obj.line_total()


class PurchaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for purchase list endpoint."""

    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        """Meta options for PurchaseListSerializer."""
        model = Purchase
        fields = [
            "id",
            "supplier_name",
            "reference_no",
            "status",
            "total_cost",
            "item_count",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "total_cost",
            "item_count",
            "created_by_name",
            "created_at",
        ]

    def get_item_count(self, obj):
        """Return number of items in the purchase."""
        return obj.items.count()


class PurchaseDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for purchase detail endpoint."""

    items = PurchaseItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        """Meta options for PurchaseDetailSerializer."""
        model = Purchase
        fields = [
            "id",
            "created_by_name",
            "supplier_name",
            "reference_no",
            "status",
            "total_cost",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by_name",
            "status",
            "total_cost",
            "items",
            "created_at",
            "updated_at",
        ]

    def validate_supplier_name(self, value):
        """Validate supplier name is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Supplier name cannot be empty.")
        return value.strip()

    def validate_reference_no(self, value):
        """Validate reference number uniqueness if provided."""
        if value:
            qs = Purchase.objects.filter(reference_no=value)
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():  # type: ignore[attr-defined]
                raise serializers.ValidationError("Reference number must be unique.")
        return value


class ConfirmPurchaseSerializer(serializers.Serializer):
    """Serializer for confirming a purchase."""

    def create(self, validated_data):
        raise NotImplementedError("Use save() to confirm purchase.")

    def update(self, instance, validated_data):
        raise NotImplementedError("Use save() to confirm purchase.")

    def validate(self, data):
        """Validate that the purchase can be confirmed."""
        purchase = self.context.get("purchase")

        if not purchase:
            raise serializers.ValidationError("Purchase not found.")

        if purchase.status != "DRAFT":
            raise serializers.ValidationError(
                f"Only DRAFT purchases can be confirmed. Current status: {purchase.status}."
            )

        if not purchase.items.exists():
            raise serializers.ValidationError("Cannot confirm a purchase without items.")

        return data

    def save(self):
        """
        Confirm purchase:
        - increase stock
        - create stock movements
        - update total_cost
        - mark purchase as confirmed
        """
        purchase = self.context["purchase"]
        user = self.context["request"].user

        with transaction.atomic():
            for item in purchase.items.select_related("product"):
                stock, _ = Stock.objects.get_or_create(  # type: ignore[attr-defined]
                    product=item.product,
                    defaults={"quantity": 0},
                )

                stock.quantity += item.quantity
                stock.save(update_fields=["quantity", "updated_at"])

                StockMovement.objects.create(  # type: ignore[attr-defined]
                    product=item.product,
                    created_by=user,
                    movement_type="IN",
                    quantity=item.quantity,
                    reference=purchase.reference_no or f"PO-{purchase.id}",
                    notes=f"Purchase {purchase.id} from {purchase.supplier_name}",
                )

            purchase.total_cost = purchase.compute_total()
            purchase.status = "CONFIRMED"
            purchase.save(update_fields=["total_cost", "status", "updated_at"])

        return purchase
