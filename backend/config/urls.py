from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoginView
from apps.okrs.dashboard_views import OrgProgressView, TeamProgressView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.okrs.urls")),
    path("api/", include("apps.reviews.urls")),
    path("api/", include("apps.feedback.urls")),
    path("api/dashboard/team-progress/", TeamProgressView.as_view(), name="dashboard-team-progress"),
    path("api/dashboard/org-progress/", OrgProgressView.as_view(), name="dashboard-org-progress"),
]
