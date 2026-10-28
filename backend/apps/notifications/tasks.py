"""
Celery tasks. Genuinely async-justified work only:

  - send_feedback_request_notification: fired immediately when a
    FeedbackRequest is created (apps/feedback/serializers.py), so request
    creation isn't blocked on an email send.
  - send_cycle_deadline_reminders: beat-scheduled (config/celery.py),
    nightly sweep for cycles approaching their end date with outstanding
    self-reviews/manager-reviews, so reminders don't require a human to
    remember to send them. Purely additive/read-driven (never mutates
    cycle or review state), so re-running it after a scheduler restart
    just resends reminders rather than corrupting anything - acceptably
    idempotent for a reminder email, unlike a state transition would be.

With CELERY_TASK_ALWAYS_EAGER=True (the default - see
config/settings/base.py) these run synchronously, so tests exercise the
real logic without a broker.
"""
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone


@shared_task
def send_feedback_request_notification(feedback_request_id):
    from apps.feedback.models import FeedbackRequest

    try:
        fr = FeedbackRequest.objects.select_related("subject", "reviewer", "requested_by", "cycle").get(
            pk=feedback_request_id
        )
    except FeedbackRequest.DoesNotExist:
        return f"FeedbackRequest {feedback_request_id} no longer exists"

    body = render_to_string(
        "notifications/feedback_request.txt",
        {
            "reviewer_name": fr.reviewer.get_full_name() or fr.reviewer.email,
            "requester_name": (fr.requested_by.get_full_name() or fr.requested_by.email)
            if fr.requested_by
            else "HR",
            "subject_name": fr.subject.get_full_name() or fr.subject.email,
            "relationship": fr.relationship,
            "cycle_name": fr.cycle.name,
        },
    )
    send_mail(
        subject=f"Feedback requested: {fr.subject.get_full_name() or fr.subject.email}",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[fr.reviewer.email],
    )
    return f"Sent feedback-request email for FeedbackRequest {feedback_request_id}"


@shared_task
def send_cycle_deadline_reminders():
    from apps.reviews.models import ReviewCycle, SelfReview

    today = timezone.now().date()
    window = today + timedelta(days=settings.CYCLE_DEADLINE_REMINDER_WINDOW_DAYS)
    sent = 0

    due_cycles = ReviewCycle.objects.filter(
        end_date__gte=today, end_date__lte=window
    ).exclude(status=ReviewCycle.Status.CLOSED)

    for cycle in due_cycles:
        if cycle.status == ReviewCycle.Status.SELF_REVIEW:
            pending_employees = cycle.objectives.exclude(
                owner__self_reviews__cycle=cycle, owner__self_reviews__submitted_at__isnull=False
            ).values_list("owner", flat=True).distinct()
            from apps.accounts.models import User

            for user in User.objects.filter(id__in=pending_employees):
                body = render_to_string(
                    "notifications/cycle_deadline_reminder.txt",
                    {
                        "user_name": user.get_full_name() or user.email,
                        "cycle_name": cycle.name,
                        "cycle_status": cycle.status,
                        "end_date": cycle.end_date,
                        "pending_items": ["Submit your self-review"],
                    },
                )
                send_mail(
                    subject=f"Reminder: {cycle.name} self-review due {cycle.end_date}",
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                )
                sent += 1
    return f"Sent {sent} deadline reminder email(s)"
