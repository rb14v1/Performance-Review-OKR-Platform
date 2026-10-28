from django.test import TestCase

from apps.accounts.models import User
from apps.feedback.models import CalibrationEntry, CalibrationSession
from apps.accounts.models import Department
from apps.reviews.models import CycleStatusAudit, ManagerReview, ReviewCycle
from apps.reviews.state_machine import GuardConditionError, IllegalTransitionError, transition


class StateMachineTests(TestCase):
    def setUp(self):
        self.hr_admin = User.objects.create_user(
            email="hr@co.com", password="pw12345678", role=User.Role.HR_ADMIN
        )
        self.manager = User.objects.create_user(
            email="mgr@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.employee = User.objects.create_user(
            email="emp@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager
        )
        self.cycle = ReviewCycle.objects.create(
            name="H1", start_date="2026-01-01", end_date="2026-06-30"
        )

    def test_happy_path_forward_transitions(self):
        for next_status in [
            ReviewCycle.Status.SELF_REVIEW,
            ReviewCycle.Status.MANAGER_REVIEW,
            ReviewCycle.Status.PEER_FEEDBACK,
        ]:
            transition(self.cycle, next_status, actor=self.hr_admin)
            self.cycle.refresh_from_db()
            self.assertEqual(self.cycle.status, next_status)

        # Submit the manager review so CALIBRATION's guard passes cleanly.
        ManagerReview.objects.create(
            cycle=self.cycle,
            employee=self.employee,
            manager=self.manager,
            manager_at_cycle_start=self.manager,
            submitted_at="2026-03-01T00:00:00Z",
        )
        transition(self.cycle, ReviewCycle.Status.CALIBRATION, actor=self.hr_admin)
        self.cycle.refresh_from_db()
        self.assertEqual(self.cycle.status, ReviewCycle.Status.CALIBRATION)

        department = Department.objects.create(name="Eng")
        session = CalibrationSession.objects.create(
            cycle=self.cycle, department=department, facilitator=self.hr_admin
        )
        CalibrationEntry.objects.create(
            session=session, employee=self.employee, pre_rating="meets", post_rating="meets", resolved=True
        )
        transition(self.cycle, ReviewCycle.Status.CLOSED, actor=self.hr_admin)
        self.cycle.refresh_from_db()
        self.assertEqual(self.cycle.status, ReviewCycle.Status.CLOSED)

        audits = CycleStatusAudit.objects.filter(cycle=self.cycle).order_by("created_at")
        self.assertEqual(
            [a.to_status for a in audits],
            [
                ReviewCycle.Status.SELF_REVIEW,
                ReviewCycle.Status.MANAGER_REVIEW,
                ReviewCycle.Status.PEER_FEEDBACK,
                ReviewCycle.Status.CALIBRATION,
                ReviewCycle.Status.CLOSED,
            ],
        )
        self.assertTrue(all(not a.was_override for a in audits))

    def test_illegal_jump_raises(self):
        with self.assertRaises(IllegalTransitionError):
            transition(self.cycle, ReviewCycle.Status.PEER_FEEDBACK, actor=self.hr_admin)
        self.cycle.refresh_from_db()
        self.assertEqual(self.cycle.status, ReviewCycle.Status.DRAFT)

    def test_illegal_backward_transition_raises(self):
        transition(self.cycle, ReviewCycle.Status.SELF_REVIEW, actor=self.hr_admin)
        with self.assertRaises(IllegalTransitionError):
            transition(self.cycle, ReviewCycle.Status.DRAFT, actor=self.hr_admin)

    def test_calibration_blocked_without_all_manager_reviews_submitted(self):
        transition(self.cycle, ReviewCycle.Status.SELF_REVIEW, actor=self.hr_admin)
        transition(self.cycle, ReviewCycle.Status.MANAGER_REVIEW, actor=self.hr_admin)
        transition(self.cycle, ReviewCycle.Status.PEER_FEEDBACK, actor=self.hr_admin)

        ManagerReview.objects.create(
            cycle=self.cycle,
            employee=self.employee,
            manager=self.manager,
            manager_at_cycle_start=self.manager,
            submitted_at=None,  # not submitted
        )
        with self.assertRaises(GuardConditionError):
            transition(self.cycle, ReviewCycle.Status.CALIBRATION, actor=self.hr_admin)
        self.cycle.refresh_from_db()
        self.assertEqual(self.cycle.status, ReviewCycle.Status.PEER_FEEDBACK)

    def test_hr_override_forces_calibration_entry_and_is_audited(self):
        transition(self.cycle, ReviewCycle.Status.SELF_REVIEW, actor=self.hr_admin)
        transition(self.cycle, ReviewCycle.Status.MANAGER_REVIEW, actor=self.hr_admin)
        transition(self.cycle, ReviewCycle.Status.PEER_FEEDBACK, actor=self.hr_admin)

        ManagerReview.objects.create(
            cycle=self.cycle,
            employee=self.employee,
            manager=self.manager,
            manager_at_cycle_start=self.manager,
            submitted_at=None,
        )
        transition(
            self.cycle,
            ReviewCycle.Status.CALIBRATION,
            actor=self.hr_admin,
            override_reason="Manager on leave; proceeding per VP approval.",
        )
        self.cycle.refresh_from_db()
        self.assertEqual(self.cycle.status, ReviewCycle.Status.CALIBRATION)

        audit = CycleStatusAudit.objects.get(cycle=self.cycle, to_status=ReviewCycle.Status.CALIBRATION)
        self.assertTrue(audit.was_override)
        self.assertIn("VP approval", audit.override_reason)

    def test_non_hr_admin_cannot_override(self):
        transition(self.cycle, ReviewCycle.Status.SELF_REVIEW, actor=self.hr_admin)
        transition(self.cycle, ReviewCycle.Status.MANAGER_REVIEW, actor=self.hr_admin)
        transition(self.cycle, ReviewCycle.Status.PEER_FEEDBACK, actor=self.hr_admin)
        ManagerReview.objects.create(
            cycle=self.cycle,
            employee=self.employee,
            manager=self.manager,
            manager_at_cycle_start=self.manager,
            submitted_at=None,
        )
        with self.assertRaises(GuardConditionError):
            transition(
                self.cycle,
                ReviewCycle.Status.CALIBRATION,
                actor=self.manager,
                override_reason="I really want to",
            )
