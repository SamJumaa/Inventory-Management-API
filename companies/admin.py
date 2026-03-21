from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "is_active", "created_at")
    search_fields = ("name", "email", "phone")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("is_active", "created_at")
