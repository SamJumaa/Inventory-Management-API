from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CompanyOwnedModel(TimeStampedModel):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)ss",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_%(class)ss",
    )

    class Meta:
        abstract = True
