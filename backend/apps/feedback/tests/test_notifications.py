from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.reviews.models import ReviewCycle


class FeedbackRequestNotificationTests(APITestCase):
    """With CELERY_TASK_ALWAYS_EAGER=True (config/settings/test.py), the
    feedback-request notification Celery task runs synchronously inside the
    request/response cycle, so we can assert on django.core.mail.outbox
    directly without a broker/worker."""

    def setUp(self):
        self.hr_admin = User.objects.create_user(
            email="hr@co.com", password="pw12345678", role=User.Role.HR_ADMIN
        )
        self.subject = User.objects.create_user(email="subject@co.com", password="pw12345678")
        self.reviewer = User.objects.create_user(email="reviewer@co.com", password="pw12345678")
        self.cycle = ReviewCycle.objects.create(
            name="H1", start_date="2026-01-01", end_date="2026-06-30"
        )

    def test_creating_feedback_request_sends_email_synchronously(self):
        self.client.force_authenticate(self.hr_admin)
        url = reverse("feedback-request-list")
        resp = self.client.post(
            url,
            {
                "cycle": self.cycle.id,
                "subject": self.subject.id,
                "reviewer": self.reviewer.id,
                "relationship": "peer",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.reviewer.email, mail.outbox[0].to)
