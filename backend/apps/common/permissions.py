"""
Shared role-permission classes.

Combined with queryset-level scoping in each app's views (never
serializer-only hiding) - see apps/accounts/views.py for the
direct-reports-only manager scoping and apps/feedback/permissions.py for
the peer-feedback anonymity + release-threshold logic.
"""
from rest_framework.permissions import BasePermission


def user_role(request):
    user = getattr(request, "user", None)
    return getattr(user, "role", None)


class IsEmployee(BasePermission):
    """Any authenticated user acting in the baseline employee capacity
    (every role is also an employee for self-service endpoints)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and user_role(request) == "manager"
        )


class IsHRAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and user_role(request) == "hr_admin"
        )


class IsManagerOrHRAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and user_role(request) in ("manager", "hr_admin")
        )
