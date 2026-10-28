from django.conf import settings
from django.db import models


class ReviewCycle(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SELF_REVIEW = "self_review", "Self Review"
        MANAGER_REVIEW = "manager_review", "Manager Review"
        PEER_FEEDBACK = "peer_feedback", "Peer Feedback"
        CALIBRATION = "calibration", "Calibration"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.status})"


class CycleStatusAudit(models.Model):
    """Audit trail for every cycle status transition, including the HR
    override path (entering CALIBRATION before all ManagerReviews are
    submitted requires a required override_reason, persisted here)."""

    cycle = models.ForeignKey(ReviewCycle, on_delete=models.CASCADE, related_name="status_audits")
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="cycle_transitions"
    )
    was_override = models.BooleanField(default=False)
    override_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.cycle_id}: {self.from_status} -> {self.to_status}"


class SelfReview(models.Model):
    cycle = models.ForeignKey(ReviewCycle, on_delete=models.CASCADE, related_name="self_reviews")
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="self_reviews"
    )
    accomplishments = models.TextField(blank=True, default="")
    challenges = models.TextField(blank=True, default="")
    self_rating = models.CharField(max_length=50, blank=True, default="")
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cycle", "employee")

    def __str__(self):
        return f"SelfReview({self.employee_id}, {self.cycle_id})"


class ManagerReview(models.Model):
    cycle = models.ForeignKey(ReviewCycle, on_delete=models.CASCADE, related_name="manager_reviews")
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="manager_reviews_received"
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="manager_reviews_authored"
    )
    # Snapshot of employee.manager AT THE TIME this review was created. Used
    # for all historical visibility scoping instead of the live `manager`
    # FK on User, so a mid-cycle reassignment never retroactively moves
    # historical review access to the new manager (nor strips it from the
    # original one).
    manager_at_cycle_start = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="manager_reviews_snapshotted",
    )
    draft_rating = models.CharField(max_length=50, blank=True, default="")
    comments = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cycle", "employee")
        ordering = ["id"]

    def __str__(self):
        return f"ManagerReview({self.employee_id}, {self.cycle_id})"


class Rating(models.Model):
    class Source(models.TextChoices):
        MANAGER = "manager", "Manager"
        CALIBRATION = "calibration", "Calibration"

    cycle = models.ForeignKey(ReviewCycle, on_delete=models.CASCADE, related_name="ratings")
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings"
    )
    # Same snapshot rationale as ManagerReview.manager_at_cycle_start.
    manager_at_cycle_start = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ratings_snapshotted",
    )
    final_rating = models.CharField(max_length=50, blank=True, default="")
    rating_source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANAGER)
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ratings_finalized"
    )
    finalized_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by_employee = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cycle", "employee")

    def __str__(self):
        return f"Rating({self.employee_id}, {self.cycle_id}, {self.final_rating})"
