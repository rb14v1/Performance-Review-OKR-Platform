from django.conf import settings
from django.db import models


class FeedbackRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    class Relationship(models.TextChoices):
        PEER = "peer", "Peer"
        MANAGER = "manager", "Manager"
        DIRECT_REPORT = "direct_report", "Direct Report"
        SELF = "self", "Self"

    cycle = models.ForeignKey(
        "reviews.ReviewCycle", on_delete=models.CASCADE, related_name="feedback_requests"
    )
    subject = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedback_requests_about_me"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedback_requests_assigned_to_me"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="feedback_requests_made"
    )
    relationship = models.CharField(max_length=20, choices=Relationship.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("cycle", "subject", "reviewer")

    def __str__(self):
        return f"FeedbackRequest({self.reviewer_id} -> {self.subject_id}, {self.status})"


class PeerFeedback(models.Model):
    class AnonymityMode(models.TextChoices):
        ANONYMOUS = "anonymous", "Anonymous"
        NAMED = "named", "Named"

    cycle = models.ForeignKey("reviews.ReviewCycle", on_delete=models.CASCADE, related_name="peer_feedback")
    subject = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="peer_feedback_about_me"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="peer_feedback_authored"
    )
    feedback_request = models.OneToOneField(
        FeedbackRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="submission"
    )
    relationship = models.CharField(max_length=20, choices=FeedbackRequest.Relationship.choices)
    anonymity_mode = models.CharField(
        max_length=20, choices=AnonymityMode.choices, default=AnonymityMode.ANONYMOUS
    )
    strengths = models.TextField(blank=True, default="")
    improvements = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cycle", "subject", "reviewer")

    def __str__(self):
        return f"PeerFeedback({self.subject_id}, {self.cycle_id}, {self.anonymity_mode})"


class PeerFeedbackAccessLog(models.Model):
    """Audit row written every time an HR admin views a PeerFeedback entry's
    RAW (un-anonymized) reviewer identity."""

    accessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    subject = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    cycle = models.ForeignKey("reviews.ReviewCycle", on_delete=models.CASCADE, related_name="+")
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-accessed_at"]

    def __str__(self):
        return f"PeerFeedbackAccessLog({self.accessed_by_id} -> {self.subject_id}@{self.cycle_id})"


class CalibrationSession(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    cycle = models.ForeignKey(
        "reviews.ReviewCycle", on_delete=models.CASCADE, related_name="calibration_sessions"
    )
    department = models.ForeignKey(
        "accounts.Department", on_delete=models.CASCADE, related_name="calibration_sessions"
    )
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="calibration_sessions_run"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cycle", "department")

    def __str__(self):
        return f"CalibrationSession({self.department_id}, {self.cycle_id})"


class CalibrationEntry(models.Model):
    session = models.ForeignKey(CalibrationSession, on_delete=models.CASCADE, related_name="entries")
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="calibration_entries"
    )
    pre_rating = models.CharField(max_length=50)
    post_rating = models.CharField(max_length=50, blank=True, default="")
    adjustment_reason = models.TextField(blank=True, default="")
    # Set True once the committee has made (or explicitly confirmed) its
    # calibration decision for this employee. ReviewCycle cannot close while
    # any CalibrationEntry in it is unresolved (see
    # apps/reviews/state_machine.py).
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("session", "employee")

    def __str__(self):
        return f"CalibrationEntry({self.employee_id}, {self.session_id})"
