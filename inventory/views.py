"""
ViewSets for inventory app: Stock and StockMovement.
"""

from django.db.models import F
from django.utils.dateparse import parse_date
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Stock, StockMovement
from .serializers import AdjustStockSerializer, StockMovementSerializer, StockSerializer


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoints for stock."""

    queryset = Stock.objects.select_related("product", "product__category").all()  # type: ignore[attr-defined]
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["quantity", "product__name"]
    ordering = ["product__name"]
    pagination_class = None


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoints for stock movement audit log."""

    queryset = StockMovement.objects.select_related(  # type: ignore[attr-defined]
        "product",
        "product__category",
        "created_by",
    ).all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["product", "movement_type", "created_by"]
    search_fields = ["reference", "notes", "product__sku", "product__name"]
    ordering_fields = ["created_at", "quantity", "product__name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if date_from:
            from_date = parse_date(date_from)
            if from_date:
                qs = qs.filter(created_at__date__gte=from_date)

        if date_to:
            to_date = parse_date(date_to)
            if to_date:
                qs = qs.filter(created_at__date__lte=to_date)

        return qs


class InventoryViewSet(viewsets.ViewSet):
    """Inventory operations: adjust and low-stock."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="adjust")
    def adjust(self, request):
        serializer = AdjustStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stock = serializer.save(user=request.user)
        return Response(StockSerializer(stock).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, _request):
        items = (
            Stock.objects.filter(quantity__lt=F("product__reorder_level"))  # type: ignore[attr-defined]
            .select_related("product", "product__category")
            .order_by("product__name")
        )

        data = StockSerializer(items, many=True).data
        return Response({"count": len(data), "results": data}, status=status.HTTP_200_OK)
