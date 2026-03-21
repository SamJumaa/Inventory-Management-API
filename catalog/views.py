"""
ViewSets for catalog app: Category and Product.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated
from common.mixins import CompanyQuerySetMixin
from common.permissions import IsCompanyAdminOrReadOnly

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


class CategoryViewSet(CompanyQuerySetMixin, viewsets.ModelViewSet):
    """Category CRUD endpoints."""

    queryset = Category.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return super().get_queryset().prefetch_related("products")

    def get_serializer_class(self):
        return CategorySerializer


class ProductViewSet(CompanyQuerySetMixin, viewsets.ModelViewSet):
    """Product CRUD endpoints with filtering, search, and ordering."""

    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated, IsCompanyAdminOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "sku"]
    ordering_fields = ["name", "sku", "unit_price", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return super().get_queryset().select_related("category")

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer
