from django.db.models import Q
from rest_framework import mixins, permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.okrs.models import CheckIn, KeyResult, Objective
from apps.okrs.serializers import (
    CheckInSerializer,
    KeyResultSerializer,
    ObjectiveDetailSerializer,
    ObjectiveListSerializer,
    ObjectiveWriteSerializer,
)


class ObjectiveViewSet(viewsets.ModelViewSet):
    """Queryset scoping (not serializer-only hiding):
      - hr_admin: every objective, org-wide.
      - manager: own objectives + their direct reports' objectives.
      - employee: own objectives only.
    """

    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["cycle", "status", "owner"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ObjectiveDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return ObjectiveWriteSerializer
        return ObjectiveListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Objective.objects.select_related("owner", "cycle").all()
        if user.role == "hr_admin":
            return qs
        if user.role == "manager":
            return qs.filter(Q(owner=user) | Q(owner__manager=user))
        return qs.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class KeyResultViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = KeyResultSerializer
    filterset_fields = ["objective"]

    def get_queryset(self):
        user = self.request.user
        qs = KeyResult.objects.select_related("objective", "objective__owner").all()
        if user.role == "hr_admin":
            return qs
        if user.role == "manager":
            return qs.filter(Q(objective__owner=user) | Q(objective__owner__manager=user))
        return qs.filter(objective__owner=user)

    def perform_create(self, serializer):
        objective = serializer.validated_data["objective"]
        user = self.request.user
        if user.role != "hr_admin" and objective.owner_id != user.id:
            raise PermissionDenied("You can only add key results to your own objectives.")
        serializer.save()


class CheckInViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Append-only: only create + list are exposed. No update/destroy -
    CheckIn history must always be re-derivable and immutable."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CheckInSerializer
    filterset_fields = ["key_result"]

    def get_queryset(self):
        user = self.request.user
        qs = CheckIn.objects.select_related("key_result", "key_result__objective", "created_by").all()
        if user.role == "hr_admin":
            return qs
        if user.role == "manager":
            return qs.filter(
                Q(key_result__objective__owner=user) | Q(key_result__objective__owner__manager=user)
            )
        return qs.filter(key_result__objective__owner=user)

    def perform_create(self, serializer):
        key_result = serializer.validated_data["key_result"]
        user = self.request.user
        if user.role != "hr_admin" and key_result.objective.owner_id != user.id:
            raise PermissionDenied("You can only check in on your own key results.")
        serializer.save()
