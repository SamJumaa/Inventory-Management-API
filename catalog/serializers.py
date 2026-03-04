"""
Serializers for catalog app: Category and Product.
"""

from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    product_count = serializers.SerializerMethodField()

    class Meta:
        """Meta options for CategorySerializer."""
        model = Category
        fields = ["id", "name", "description", "product_count", "created_at", "updated_at"]
        read_only_fields = ["id", "product_count", "created_at", "updated_at"]

    def get_product_count(self, obj):
        """Returns the count of active products in this category."""
        return obj.products.filter(is_active=True).count()


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing products."""
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        """Meta options for ProductListSerializer."""
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "category",
            "category_name",
            "unit_price",
            "reorder_level",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for product create/update/read."""
    category = CategorySerializer(read_only=True)

    # This is the IMPORTANT fix:
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),  # type: ignore[attr-defined]
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        """Meta options for ProductDetailSerializer."""
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "category",
            "category_id",
            "description",
            "unit_price",
            "reorder_level",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_sku(self, value):
        """ Ensure SKU is not empty and is uppercase."""
        if not value or not value.strip():
            raise serializers.ValidationError("SKU cannot be empty.")
        return value.strip().upper()
