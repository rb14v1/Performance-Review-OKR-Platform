"""
Review cycle state machine.

Forward-only transition map:

    draft -> self_review -> manager_review -> peer_feedback -> calibration -> closed

Anything else (skipping a stage, going backward) is illegal and
`transition()` raises IllegalTransitionError (-> HTTP 409 at the API
layer).

Guard conditions:
  - Entering CALIBRATION requires every ManagerReview for the cycle to be
    submitted, UNLESS an HR admin forces it with a required
    `override_reason` - the override is always recorded on a
    CycleStatusAudit row (was_override=True) regardless of outcome.
  - Entering CLOSED requires every CalibrationEntry across the cycle's
    CalibrationSessions to be resolved (post_rating assigned).
  - Every transition (forced or not) writes a CycleStatusAudit row, so the
    cycle's full history is reconstructable.
"""
from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import ConflictError
from apps.reviews.models import CycleStatusAudit, ManagerReview, ReviewCycle

ORDER = [
    ReviewCycle.Status.DRAFT,
    ReviewCycle.Status.SELF_REVIEW,
    ReviewCycle.Status.MANAGER_REVIEW,
    ReviewCycle.Status.PEER_FEEDBACK,
    ReviewCycle.Status.CALIBRATION,
    ReviewCycle.Status.CLOSED,
]
NEXT_STATUS = {ORDER[i]: ORDER[i + 1] for i in range(len(ORDER) - 1)}


class IllegalTransitionError(ConflictError):
    pass


class GuardConditionError(ConflictError):
    pass


def _manager_reviews_incomplete(cycle):
    return ManagerReview.objects.filter(cycle=cycle, submitted_at__isnull=True).exists()


def _calibration_unresolved(cycle):
    # Local import: apps.feedback depends on apps.reviews (FK to
    # ReviewCycle), so importing feedback models at module scope here would
    # risk a circular import during app loading. Deferring the import to
    # call time (after both apps are fully loaded) avoids that.
    from apps.feedback.models import CalibrationEntry

    return CalibrationEntry.objects.filter(session__cycle=cycle, resolved=False).exists()


@transaction.atomic
def transition(cycle: ReviewCycle, new_status: str, *, actor, override_reason: str = ""):
    """Advance `cycle` to `new_status`. Raises IllegalTransitionError for
    any non-forward-adjacent move, and GuardConditionError if a stage's
    entry requirements aren't met (unless `actor` is an HR admin supplying
    `override_reason`, which is recorded as an audit override)."""
    current = cycle.status
    expected_next = NEXT_STATUS.get(current)
    is_hr_admin = bool(actor and getattr(actor, "role", None) == "hr_admin")

    if expected_next is None or new_status != expected_next:
        raise IllegalTransitionError(
            f"Cannot transition cycle from '{current}' to '{new_status}'.",
            detail={
                "current_status": current,
                "requested_status": new_status,
                "allowed_next_status": expected_next,
            },
        )

    was_override = False

    if new_status == ReviewCycle.Status.CALIBRATION and _manager_reviews_incomplete(cycle):
        if is_hr_admin and override_reason:
            was_override = True
        else:
            raise GuardConditionError(
                "Cannot enter calibration: not all manager reviews for this cycle "
                "are submitted. An HR admin may force this with an override_reason.",
                detail={"reason": "incomplete_manager_reviews"},
            )

    if new_status == ReviewCycle.Status.CLOSED and _calibration_unresolved(cycle):
        if is_hr_admin and override_reason:
            was_override = True
        else:
            raise GuardConditionError(
                "Cannot close cycle: not all calibration entries are resolved. "
                "An HR admin may force this with an override_reason.",
                detail={"reason": "unresolved_calibration_entries"},
            )

    cycle.status = new_status
    cycle.save(update_fields=["status"])

    CycleStatusAudit.objects.create(
        cycle=cycle,
        from_status=current,
        to_status=new_status,
        actor=actor,
        was_override=was_override,
        override_reason=override_reason if was_override else "",
    )
    return cycle
