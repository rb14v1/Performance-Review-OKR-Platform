from decimal import Decimal

from django.conf import settings
from django.db import models


class Objective(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="objectives"
    )
    cycle = models.ForeignKey(
        "reviews.ReviewCycle", on_delete=models.CASCADE, related_name="objectives"
    )
    # Alignment: an objective may roll up into a parent objective (e.g. an
    # individual objective aligned under a team/department objective).
    parent_objective = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="child_objectives",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    # Cached, recomputed on write (CheckIn create / KR change) - never
    # recomputed on read. See apps/okrs/services.py.
    progress_pct = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class KeyResult(models.Model):
    class MetricType(models.TextChoices):
        NUMBER = "number", "Number"
        PERCENTAGE = "percentage", "Percentage"
        BOOLEAN = "boolean", "Boolean"
        CURRENCY = "currency", "Currency"

    objective = models.ForeignKey(Objective, on_delete=models.CASCADE, related_name="key_results")
    title = models.CharField(max_length=255)
    metric_type = models.CharField(max_length=20, choices=MetricType.choices)
    start_value = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    target_value = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("100"))
    current_value = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    # Optional per-KR weight for the objective's weighted-average rollup.
    # NULL = equal weight alongside any other unweighted KRs.
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    progress_pct = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.title} ({self.objective_id})"


class CheckIn(models.Model):
    """Append-only progress log. Never updated or deleted after creation -
    the KeyResult's current_value/progress_pct (and the Objective's cached
    rollup) are always re-derivable from the full CheckIn history."""

    class Confidence(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    key_result = models.ForeignKey(KeyResult, on_delete=models.CASCADE, related_name="check_ins")
    value = models.DecimalField(max_digits=14, decimal_places=2)
    confidence_level = models.CharField(
        max_length=10, choices=Confidence.choices, default=Confidence.MEDIUM
    )
    comment = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="check_ins"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"CheckIn({self.key_result_id}, {self.value})"
