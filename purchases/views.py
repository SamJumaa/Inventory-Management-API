"""
ViewSets for purchases app: Purchase.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Purchase
from .serializers import (
    ConfirmPurchaseSerializer,
    PurchaseDetailSerializer,
    PurchaseListSerializer,
)


class PurchaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Purchase CRUD and confirm action.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "created_by"]
    search_fields = ["supplier_name", "reference_no"]
    ordering_fields = ["created_at", "total_cost", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Return purchases with related data optimized."""
        return Purchase.objects.select_related("created_by").prefetch_related(
            "items",
            "items__product",
        ).all()  # type: ignore[attr-defined]

    def get_serializer_class(self):
        """Use list serializer for list, detail serializer for others."""
        if self.action == "list":
            return PurchaseListSerializer
        return PurchaseDetailSerializer

    def perform_create(self, serializer):
        """Set created_by to current user on creation."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Only allow updating DRAFT purchases."""
        purchase = self.get_object()
        if purchase.status != "DRAFT":
            raise ValidationError(
                f"Cannot update a {purchase.status} purchase. Only DRAFT purchases can be modified."
            )
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow deleting DRAFT purchases."""
        if instance.status != "DRAFT":
            raise ValidationError(
                f"Cannot delete a {instance.status} purchase. Only DRAFT purchases can be deleted."
            )
        instance.delete()

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """
        Confirm a purchase and update stock.
        """
        purchase = self.get_object()

        serializer = ConfirmPurchaseSerializer(
            data={},
            context={"purchase": purchase, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        purchase = serializer.save()

        response_serializer = PurchaseDetailSerializer(purchase)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
