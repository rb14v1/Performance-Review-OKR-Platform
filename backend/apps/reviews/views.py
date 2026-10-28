from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.common.permissions import IsHRAdmin
from apps.reviews.models import ManagerReview, Rating, ReviewCycle, SelfReview
from apps.reviews.serializers import (
    CycleTransitionSerializer,
    ManagerReviewSerializer,
    ManagerReviewSubmitSerializer,
    RatingAcknowledgeSerializer,
    RatingFinalizeSerializer,
    RatingSerializer,
    ReviewCycleSerializer,
    SelfReviewSerializer,
    SelfReviewSubmitSerializer,
)
from apps.reviews.state_machine import transition


class ReviewCycleViewSet(viewsets.ModelViewSet):
    queryset = ReviewCycle.objects.all()
    serializer_class = ReviewCycleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "transition"):
            return [IsHRAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        cycle = self.get_object()
        serializer = CycleTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cycle = transition(
            cycle,
            serializer.validated_data["new_status"],
            actor=request.user,
            override_reason=serializer.validated_data.get("override_reason", ""),
        )
        return Response(ReviewCycleSerializer(cycle).data)


class SelfReviewViewSet(viewsets.ModelViewSet):
    serializer_class = SelfReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["cycle"]

    def get_queryset(self):
        user = self.request.user
        qs = SelfReview.objects.select_related("employee", "cycle").all()
        if user.role == "hr_admin":
            return qs
        if user.role == "manager":
            return qs.filter(Q(employee=user) | Q(employee__manager=user))
        return qs.filter(employee=user)

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        instance = self.get_object()
        if instance.employee_id != request.user.id:
            raise PermissionDenied("You can only submit your own self-review.")
        serializer = SelfReviewSubmitSerializer(instance=instance, data={})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SelfReviewSerializer(instance).data)


class ManagerReviewViewSet(viewsets.ModelViewSet):
    """Queryset scoping uses the SNAPSHOT (manager_at_cycle_start), not the
    employee's live `manager` FK - this is what makes historical review
    visibility immune to mid-cycle reassignment. A manager can only ever
    retrieve a ManagerReview they themselves authored/snapshotted into, even
    by guessing an ID."""

    serializer_class = ManagerReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["cycle", "employee"]

    def get_queryset(self):
        user = self.request.user
        qs = ManagerReview.objects.select_related("employee", "manager", "manager_at_cycle_start").all()
        if user.role == "hr_admin":
            return qs
        if user.role == "manager":
            return qs.filter(manager_at_cycle_start=user)
        return qs.filter(employee=user)

    def perform_create(self, serializer):
        request = self.request
        employee = serializer.validated_data["employee"]
        if request.user.role != "hr_admin" and employee.manager_id != request.user.id:
            raise PermissionDenied("You can only write manager reviews for your direct reports.")
        serializer.save()

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        instance = self.get_object()
        if instance.manager_at_cycle_start_id != request.user.id and request.user.role != "hr_admin":
            raise PermissionDenied("You can only submit your own manager reviews.")
        serializer = ManagerReviewSubmitSerializer(instance=instance, data={})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ManagerReviewSerializer(instance).data)


class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["cycle", "employee"]

    def get_queryset(self):
        user = self.request.user
        qs = Rating.objects.select_related("employee", "manager_at_cycle_start").all()
        if user.role == "hr_admin":
            return qs
        if user.role == "manager":
            return qs.filter(manager_at_cycle_start=user)
        return qs.filter(employee=user)

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "finalize"):
            return [IsHRAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        employee = serializer.validated_data["employee"]
        serializer.save(manager_at_cycle_start=employee.manager)

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        instance = self.get_object()
        serializer = RatingFinalizeSerializer(
            instance=instance, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RatingSerializer(instance).data)

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        instance = self.get_object()
        if instance.employee_id != request.user.id:
            raise PermissionDenied("You can only acknowledge your own rating.")
        if not instance.finalized_at:
            raise ValidationError("Rating has not been finalized yet.")
        serializer = RatingAcknowledgeSerializer(instance=instance, data={})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RatingSerializer(instance).data)
