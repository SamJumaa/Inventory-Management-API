from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("staff", "Staff"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="user_profiles",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="staff")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.company.name if self.company else 'No Company'}"
