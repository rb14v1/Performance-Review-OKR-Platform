from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import Department, User
from apps.accounts.serializers import (
    DepartmentSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from apps.common.permissions import IsHRAdmin


class LoginView(TokenObtainPairView):
    """POST {email, password} -> {access, refresh}. Role is embedded in the
    User model and re-fetched server-side on every request (DRF
    authenticates by user id, not by trusting client-held claims), so a
    stale/forged role claim can never grant access."""


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    """Org-wide user directory. Only HR admins can list/create/edit other
    users; everyone can read via /me/. Non-admins get a read-only,
    org-directory view (needed so e.g. an employee can pick a peer-feedback
    reviewer)."""

    serializer_class = UserSerializer
    queryset = User.objects.select_related("manager", "department").all().order_by("email")
    filterset_fields = ["role", "department"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsHRAdmin()]
        return [permissions.IsAuthenticated()]


class DirectReportsView(generics.ListAPIView):
    """GET /api/users/direct-reports/ - the requesting manager's direct
    reports ONLY (not their full management subtree), enforced at the
    queryset level per spec: `User.objects.filter(manager=request.user)`."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(manager=self.request.user).select_related(
            "manager", "department"
        )


class OrgTreeView(APIView):
    """GET /api/users/org-tree/ - HR-admin-only full org hierarchy (flat
    list with manager_id, which the frontend assembles into a tree)."""

    permission_classes = [IsHRAdmin]

    def get(self, request):
        users = User.objects.select_related("manager", "department").all().order_by("email")
        return Response(UserSerializer(users, many=True).data)


class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    queryset = Department.objects.all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsHRAdmin()]
        return [permissions.IsAuthenticated()]
