"""
ViewSets for catalog app: Category and Product.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Category, Product
from .serializers import CategorySerializer, ProductDetailSerializer, ProductListSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """Category CRUD endpoints."""

    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return Category.objects.prefetch_related("products").all()

    def get_serializer_class(self):
        return CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    """Product CRUD endpoints with filtering, search, and ordering."""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "sku"]
    ordering_fields = ["name", "sku", "unit_price", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return Product.objects.select_related("category").all()

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer
