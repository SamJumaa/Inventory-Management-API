from django.db.models import F
from django.utils.dateparse import parse_date
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.mixins import CompanyQuerySetMixin
from .models import Stock, StockMovement
from .serializers import AdjustStockSerializer, StockMovementSerializer, StockSerializer


class StockViewSet(CompanyQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Stock.objects.select_related("product", "product__category")
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["quantity", "product__name"]
    ordering = ["product__name"]
    pagination_class = None


class StockMovementViewSet(CompanyQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.select_related(
        "product",
        "product__category",
        "created_by",
    )
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["product", "movement_type", "created_by"]
    search_fields = ["reference", "notes", "product__name"]
    ordering_fields = ["created_at", "quantity"]
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


class InventoryViewSet(CompanyQuerySetMixin, viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="adjust")
    def adjust(self, request):
        """
        Adjust stock: use POST only
        """
        serializer = AdjustStockSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        stock = serializer.save(user=request.user)
        return Response(StockSerializer(stock).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        company = request.user.profile.company
        items = (
            Stock.objects.filter(
                company=company, quantity__lt=F("product__reorder_level")
            )
            .select_related("product", "product__category")
            .order_by("product__name")
        )
        data = StockSerializer(items, many=True).data
        return Response({"count": len(data), "results": data})
