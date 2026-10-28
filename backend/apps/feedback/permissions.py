"""
Peer feedback anonymity + minimum-reviewer-count release gate.

Two independent protections, both enforced here (not just in serializers,
so there is a single source of truth the views and tests both call
through):

1. Identity stripping: when a PeerFeedback's anonymity_mode is
   'anonymous', the reviewer's identity must never appear in any
   serialized representation shown to the subject or their manager - only
   an HR admin may see the raw reviewer, and every such access is logged
   (PeerFeedbackAccessLog).

2. Minimum-reviewer threshold: even correctly anonymized feedback
   de-anonymizes by elimination if the pool is too small (e.g. a subject
   who knows their own team can guess "my only 2 reviewers were X and Y").
   So for the subject/manager audience, NO anonymized feedback for a given
   subject+cycle is released until at least
   settings.PEER_FEEDBACK_MIN_RELEASE_THRESHOLD submissions exist. Below
   that, the caller gets an empty/pending result - never a partial,
   de-anonymizable set.

HR admins always see everything (identity included), regardless of the
threshold - that's an intentional, audited exception, not a bypass bug.
"""
from django.conf import settings
from django.utils import timezone

from apps.feedback.models import PeerFeedback, PeerFeedbackAccessLog


def is_hr_admin(user):
    return bool(user and getattr(user, "role", None) == "hr_admin")


def submitted_count(subject, cycle):
    return PeerFeedback.objects.filter(subject=subject, cycle=cycle).count()


def threshold_met(subject, cycle):
    return submitted_count(subject, cycle) >= settings.PEER_FEEDBACK_MIN_RELEASE_THRESHOLD


def visible_peer_feedback_for(viewer, subject, cycle):
    """Return (queryset, released: bool) of PeerFeedback visible to `viewer`
    for `subject` in `cycle`.

    - HR admin: always released, full queryset, identity included -
      logs one PeerFeedbackAccessLog row per call.
    - Anyone else (the subject themselves, or the subject's manager):
      released only once the minimum-reviewer threshold is met; below
      that, released=False and the queryset is empty.
    """
    qs = PeerFeedback.objects.filter(subject=subject, cycle=cycle).select_related(
        "reviewer", "subject"
    )

    if is_hr_admin(viewer):
        PeerFeedbackAccessLog.objects.create(
            accessed_by=viewer, subject=subject, cycle=cycle, accessed_at=timezone.now()
        )
        return qs, True

    if not threshold_met(subject, cycle):
        return PeerFeedback.objects.none(), False

    return qs, True


def serialize_identity(peer_feedback, viewer):
    """Return the reviewer representation to use for a given viewer: the
    real UserBriefSerializer data if the entry is 'named' or the viewer is
    HR, else None (stripped)."""
    if peer_feedback.anonymity_mode == PeerFeedback.AnonymityMode.NAMED or is_hr_admin(viewer):
        return peer_feedback.reviewer
    return None
