from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.reviews.models import ManagerReview, Rating, ReviewCycle


class ManagerScopingTests(APITestCase):
    """Manager visibility = direct reports only; a manager cannot fetch a
    non-report's review by ID guessing. Also proves the manager snapshot
    (manager_at_cycle_start) survives a mid-cycle reassignment."""

    def setUp(self):
        self.manager_a = User.objects.create_user(
            email="mgr_a@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.manager_b = User.objects.create_user(
            email="mgr_b@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.employee = User.objects.create_user(
            email="emp@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager_a
        )
        self.other_employee = User.objects.create_user(
            email="other@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager_b
        )
        self.cycle = ReviewCycle.objects.create(
            name="H1", start_date="2026-01-01", end_date="2026-06-30"
        )
        self.review_for_b = ManagerReview.objects.create(
            cycle=self.cycle,
            employee=self.other_employee,
            manager=self.manager_b,
            manager_at_cycle_start=self.manager_b,
        )

    def test_manager_cannot_fetch_non_reports_review_by_id(self):
        self.client.force_authenticate(self.manager_a)
        url = reverse("manager-review-detail", args=[self.review_for_b.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_cannot_list_non_reports_review(self):
        self.client.force_authenticate(self.manager_a)
        url = reverse("manager-review-list")
        resp = self.client.get(url)
        ids = [row["id"] for row in resp.data["results"]] if "results" in resp.data else [
            row["id"] for row in resp.data
        ]
        self.assertNotIn(self.review_for_b.id, ids)

    def test_manager_cannot_fetch_non_reports_rating_by_id(self):
        rating_for_b = Rating.objects.create(
            cycle=self.cycle,
            employee=self.other_employee,
            manager_at_cycle_start=self.manager_b,
            final_rating="exceeds",
        )
        self.client.force_authenticate(self.manager_a)
        url = reverse("rating-detail", args=[rating_for_b.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_snapshot_survives_reassignment(self):
        review = ManagerReview.objects.create(
            cycle=self.cycle,
            employee=self.employee,
            manager=self.manager_a,
            manager_at_cycle_start=self.manager_a,
        )

        # Mid-cycle reassignment: employee now reports to manager_b.
        self.employee.manager = self.manager_b
        self.employee.save(update_fields=["manager"])

        self.client.force_authenticate(self.manager_a)
        url = reverse("manager-review-detail", args=[review.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK, "original manager retains historical access")

        self.client.force_authenticate(self.manager_b)
        resp = self.client.get(url)
        self.assertEqual(
            resp.status_code,
            status.HTTP_404_NOT_FOUND,
            "new manager does NOT retroactively gain access to a pre-reassignment review",
        )
