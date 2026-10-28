from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.feedback.models import FeedbackRequest, PeerFeedback, PeerFeedbackAccessLog
from apps.feedback.permissions import visible_peer_feedback_for
from apps.reviews.models import ReviewCycle


@override_settings(PEER_FEEDBACK_MIN_RELEASE_THRESHOLD=3)
class PeerFeedbackAnonymityTests(TestCase):
    def setUp(self):
        self.subject = User.objects.create_user(email="subject@co.com", password="pw12345678")
        self.manager = User.objects.create_user(
            email="mgr@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.subject.manager = self.manager
        self.subject.save(update_fields=["manager"])
        self.hr_admin = User.objects.create_user(
            email="hr@co.com", password="pw12345678", role=User.Role.HR_ADMIN
        )
        self.cycle = ReviewCycle.objects.create(
            name="H1", start_date="2026-01-01", end_date="2026-06-30"
        )
        self.reviewers = [
            User.objects.create_user(email=f"reviewer{i}@co.com", password="pw12345678")
            for i in range(4)
        ]

    def _submit_feedback(self, count, anonymity_mode=PeerFeedback.AnonymityMode.ANONYMOUS):
        for i in range(count):
            PeerFeedback.objects.create(
                cycle=self.cycle,
                subject=self.subject,
                reviewer=self.reviewers[i],
                relationship=FeedbackRequest.Relationship.PEER,
                anonymity_mode=anonymity_mode,
                strengths="Great collaborator",
                improvements="Could delegate more",
            )

    def test_two_reviewers_withheld_from_subject(self):
        self._submit_feedback(2)
        qs, released = visible_peer_feedback_for(self.subject, self.subject, self.cycle)
        self.assertFalse(released)
        self.assertEqual(qs.count(), 0)

    def test_two_reviewers_withheld_from_manager(self):
        self._submit_feedback(2)
        qs, released = visible_peer_feedback_for(self.manager, self.subject, self.cycle)
        self.assertFalse(released)
        self.assertEqual(qs.count(), 0)

    def test_three_reviewers_released_with_identity_stripped(self):
        self._submit_feedback(3)
        qs, released = visible_peer_feedback_for(self.subject, self.subject, self.cycle)
        self.assertTrue(released)
        self.assertEqual(qs.count(), 3)

        from apps.feedback.permissions import serialize_identity

        for entry in qs:
            self.assertIsNone(serialize_identity(entry, self.subject))

    def test_hr_admin_sees_identity_regardless_of_threshold_and_is_logged(self):
        self._submit_feedback(2)
        qs, released = visible_peer_feedback_for(self.hr_admin, self.subject, self.cycle)
        self.assertTrue(released)
        self.assertEqual(qs.count(), 2)

        from apps.feedback.permissions import serialize_identity

        for entry in qs:
            self.assertIsNotNone(serialize_identity(entry, self.hr_admin))

        self.assertEqual(
            PeerFeedbackAccessLog.objects.filter(accessed_by=self.hr_admin, subject=self.subject).count(),
            1,
        )

    def test_named_feedback_identity_visible_to_subject_once_released(self):
        self._submit_feedback(3, anonymity_mode=PeerFeedback.AnonymityMode.NAMED)
        qs, released = visible_peer_feedback_for(self.subject, self.subject, self.cycle)
        self.assertTrue(released)

        from apps.feedback.permissions import serialize_identity

        for entry in qs:
            self.assertIsNotNone(serialize_identity(entry, self.subject))
