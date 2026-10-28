from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    DepartmentViewSet,
    DirectReportsView,
    MeView,
    OrgTreeView,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("departments", DepartmentViewSet, basename="department")

urlpatterns = [
    path("users/direct-reports/", DirectReportsView.as_view(), name="user-direct-reports"),
    path("users/org-tree/", OrgTreeView.as_view(), name="user-org-tree"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
] + router.urls
