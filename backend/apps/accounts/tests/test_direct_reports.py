from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User


class DirectReportsScopingTests(APITestCase):
    """Manager visibility = direct reports only, not the full subtree."""

    def setUp(self):
        self.vp = User.objects.create_user(email="vp@co.com", password="pw12345678", role=User.Role.MANAGER)
        self.manager = User.objects.create_user(
            email="mgr@co.com", password="pw12345678", role=User.Role.MANAGER, manager=self.vp
        )
        self.report_a = User.objects.create_user(
            email="a@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager
        )
        self.report_b = User.objects.create_user(
            email="b@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager
        )
        # grandchild - should NOT show up for the VP's direct-reports call
        self.grandchild = User.objects.create_user(
            email="c@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.report_a
        )

    def test_manager_sees_only_direct_reports_not_subtree(self):
        self.client.force_authenticate(self.manager)
        resp = self.client.get(reverse("user-direct-reports"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        emails = {row["email"] for row in resp.data["results"]} if "results" in resp.data else {
            row["email"] for row in resp.data
        }
        self.assertEqual(emails, {"a@co.com", "b@co.com"})

    def test_vp_subtree_not_included_as_direct_reports(self):
        self.client.force_authenticate(self.vp)
        resp = self.client.get(reverse("user-direct-reports"))
        emails = {row["email"] for row in resp.data["results"]} if "results" in resp.data else {
            row["email"] for row in resp.data
        }
        # VP's only direct report is `manager`; the grandchild/reports are
        # NOT included even though they're in the VP's management subtree.
        self.assertEqual(emails, {"mgr@co.com"})
