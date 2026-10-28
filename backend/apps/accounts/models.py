from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    parent_department = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sub_departments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        EMPLOYEE = "employee", "Employee"
        MANAGER = "manager", "Manager"
        HR_ADMIN = "hr_admin", "HR Admin"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    # Self-referential: an employee's current manager. Queryset-level
    # scoping (apps/accounts/views.py DirectReportsView) uses
    # User.objects.filter(manager=request.user) - direct reports only, not
    # the full subtree. NOTE: this is the LIVE manager; historical reviews
    # snapshot the manager at cycle start separately (see
    # apps/reviews/models.py ManagerReview.manager_at_cycle_start) so a
    # reassignment here never retroactively moves past review visibility.
    manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="direct_reports",
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
    )
    title = models.CharField(max_length=150, blank=True, default="")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return f"{self.email} ({self.role})"
