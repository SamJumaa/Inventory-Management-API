from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "role", "created_at")
    search_fields = ("user__username", "company__name")
    list_filter = ("role", "company")
