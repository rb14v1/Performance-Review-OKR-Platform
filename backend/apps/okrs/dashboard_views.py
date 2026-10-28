from django.db.models import Avg
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Department, User
from apps.common.permissions import IsHRAdmin, IsManagerOrHRAdmin
from apps.okrs.models import Objective


class TeamProgressView(APIView):
    """GET /api/dashboard/team-progress/?cycle=<id>
    Manager: average objective progress per direct report.
    HR admin: same shape, but may pass ?manager=<id> to inspect any
    manager's team; without it, defaults to org-wide per-employee
    breakdown."""

    permission_classes = [IsManagerOrHRAdmin]

    def get(self, request):
        cycle_id = request.query_params.get("cycle")
        user = request.user

        if user.role == "manager" and not request.query_params.get("manager"):
            reports = User.objects.filter(manager=user)
        elif request.query_params.get("manager"):
            reports = User.objects.filter(manager_id=request.query_params["manager"])
        else:
            reports = User.objects.all()

        rows = []
        for report in reports:
            objectives = Objective.objects.filter(owner=report)
            if cycle_id:
                objectives = objectives.filter(cycle_id=cycle_id)
            avg_progress = objectives.aggregate(avg=Avg("progress_pct"))["avg"] or 0
            rows.append(
                {
                    "user_id": report.id,
                    "email": report.email,
                    "name": f"{report.first_name} {report.last_name}".strip(),
                    "objective_count": objectives.count(),
                    "average_progress_pct": round(float(avg_progress), 2),
                }
            )
        return Response({"results": rows})


class OrgProgressView(APIView):
    """GET /api/dashboard/org-progress/?cycle=<id> - HR-admin-only,
    average objective progress grouped by department."""

    permission_classes = [IsHRAdmin]

    def get(self, request):
        cycle_id = request.query_params.get("cycle")
        rows = []
        for department in Department.objects.all():
            objectives = Objective.objects.filter(owner__department=department)
            if cycle_id:
                objectives = objectives.filter(cycle_id=cycle_id)
            avg_progress = objectives.aggregate(avg=Avg("progress_pct"))["avg"] or 0
            rows.append(
                {
                    "department_id": department.id,
                    "department_name": department.name,
                    "objective_count": objectives.count(),
                    "average_progress_pct": round(float(avg_progress), 2),
                }
            )
        return Response({"results": rows})
