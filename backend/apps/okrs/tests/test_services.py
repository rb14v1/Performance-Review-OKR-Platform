from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.okrs.models import CheckIn, KeyResult, Objective
from apps.okrs.services import apply_check_in, recalculate_key_result, recalculate_objective
from apps.reviews.models import ReviewCycle


class ProgressRollupTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="emp@co.com", password="pw12345678")
        self.cycle = ReviewCycle.objects.create(
            name="H1", start_date="2026-01-01", end_date="2026-06-30"
        )

    def _objective(self, parent=None):
        return Objective.objects.create(
            owner=self.user, cycle=self.cycle, title="Obj", parent_objective=parent
        )

    def test_equal_weight_average(self):
        objective = self._objective()
        kr1 = KeyResult.objects.create(
            objective=objective, title="KR1", metric_type=KeyResult.MetricType.NUMBER,
            start_value=0, target_value=100, current_value=40,
        )
        kr2 = KeyResult.objects.create(
            objective=objective, title="KR2", metric_type=KeyResult.MetricType.NUMBER,
            start_value=0, target_value=100, current_value=80,
        )
        recalculate_key_result(kr1)
        recalculate_key_result(kr2)
        progress = recalculate_objective(objective)
        # (40 + 80) / 2 = 60
        self.assertEqual(progress, Decimal("60.00"))

    def test_custom_weights(self):
        objective = self._objective()
        kr1 = KeyResult.objects.create(
            objective=objective, title="KR1", metric_type=KeyResult.MetricType.NUMBER,
            start_value=0, target_value=100, current_value=0, weight=Decimal("3"),
        )
        kr2 = KeyResult.objects.create(
            objective=objective, title="KR2", metric_type=KeyResult.MetricType.NUMBER,
            start_value=0, target_value=100, current_value=100, weight=Decimal("1"),
        )
        recalculate_key_result(kr1)
        recalculate_key_result(kr2)
        progress = recalculate_objective(objective)
        # (0*3 + 100*1) / 4 = 25
        self.assertEqual(progress, Decimal("25.00"))

    def test_boolean_metric_normalization(self):
        objective = self._objective()
        kr = KeyResult.objects.create(
            objective=objective, title="Shipped?", metric_type=KeyResult.MetricType.BOOLEAN,
            start_value=0, target_value=1, current_value=0,
        )
        self.assertEqual(recalculate_key_result(kr), Decimal("0"))

        kr.current_value = 1
        kr.save(update_fields=["current_value"])
        self.assertEqual(recalculate_key_result(kr), Decimal("100"))

    def test_two_level_alignment_rollup(self):
        parent = self._objective()
        child = self._objective(parent=parent)

        parent_kr = KeyResult.objects.create(
            objective=parent, title="Parent KR", metric_type=KeyResult.MetricType.NUMBER,
            start_value=0, target_value=100, current_value=100,
        )
        child_kr = KeyResult.objects.create(
            objective=child, title="Child KR", metric_type=KeyResult.MetricType.NUMBER,
            start_value=0, target_value=100, current_value=0,
        )
        recalculate_key_result(parent_kr)
        recalculate_key_result(child_kr)

        # Recalculating the CHILD should bubble up and update the parent's
        # progress to include the child's progress alongside its own KR.
        recalculate_objective(child)
        parent.refresh_from_db()
        # parent has: its own KR at 100, plus child objective at 0 -> avg 50
        self.assertEqual(parent.progress_pct, Decimal("50.00"))

    def test_check_in_creation_triggers_full_rollup(self):
        parent = self._objective()
        child = self._objective(parent=parent)
        parent_kr = KeyResult.objects.create(
            objective=parent, title="Parent KR", metric_type=KeyResult.MetricType.PERCENTAGE,
            start_value=0, target_value=100, current_value=0,
        )
        child_kr = KeyResult.objects.create(
            objective=child, title="Child KR", metric_type=KeyResult.MetricType.PERCENTAGE,
            start_value=0, target_value=100, current_value=0,
        )
        recalculate_key_result(parent_kr)
        recalculate_key_result(child_kr)
        recalculate_objective(parent)

        check_in = CheckIn.objects.create(
            key_result=child_kr, value=Decimal("50"), created_by=self.user
        )
        apply_check_in(check_in)

        child_kr.refresh_from_db()
        child.refresh_from_db()
        parent.refresh_from_db()
        self.assertEqual(child_kr.progress_pct, Decimal("50.00"))
        self.assertEqual(child.progress_pct, Decimal("50.00"))
        # parent: its own KR (0) + child objective (50) -> avg 25
        self.assertEqual(parent.progress_pct, Decimal("25.00"))
