"""
URL configuration for inventory app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockViewSet, StockMovementViewSet, InventoryViewSet

router = DefaultRouter()
router.register(r"stock", StockViewSet, basename="stock")
router.register(r"movements", StockMovementViewSet, basename="movement")
router.register(r"inventory", InventoryViewSet, basename="inventory")

urlpatterns = [
    path("", include(router.urls)),
]
