"""
ViewSets for sales app: Sale.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Sale
from .serializers import (
    ConfirmSaleSerializer,
    SaleDetailSerializer,
    SaleListSerializer,
)


class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Sale CRUD and confirm action.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "created_by"]
    search_fields = ["customer_name", "reference_no"]
    ordering_fields = ["created_at", "total_amount", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Return sales with related data optimized."""
        return Sale.objects.select_related("created_by").prefetch_related(
            "items",
            "items__product",
        ).all()  # type: ignore[attr-defined]

    def get_serializer_class(self):
        """Use list serializer for list, detail serializer for others."""
        if self.action == "list":
            return SaleListSerializer
        return SaleDetailSerializer

    def perform_create(self, serializer):
        """Set created_by to current user on creation."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Only allow updating DRAFT sales."""
        sale = self.get_object()
        if sale.status != "DRAFT":
            raise ValidationError(
                f"Cannot update a {sale.status} sale. Only DRAFT sales can be modified."
            )
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow deleting DRAFT sales."""
        if instance.status != "DRAFT":
            raise ValidationError(
                f"Cannot delete a {instance.status} sale. Only DRAFT sales can be deleted."
            )
        instance.delete()

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm a sale and reduce stock."""
        sale = self.get_object()

        serializer = ConfirmSaleSerializer(
            data={},
            context={"sale": sale, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()

        response_serializer = SaleDetailSerializer(sale)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
