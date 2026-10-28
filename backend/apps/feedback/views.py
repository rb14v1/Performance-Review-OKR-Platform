from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.accounts.models import User
from apps.common.permissions import IsHRAdmin
from apps.feedback.models import CalibrationEntry, CalibrationSession, FeedbackRequest, PeerFeedback
from apps.feedback.permissions import submitted_count, threshold_met, visible_peer_feedback_for
from apps.feedback.serializers import (
    CalibrationEntryAdjustSerializer,
    CalibrationEntrySerializer,
    CalibrationSessionSerializer,
    FeedbackRequestCreateSerializer,
    FeedbackRequestRespondSerializer,
    FeedbackRequestSerializer,
    PeerFeedbackCreateSerializer,
    PeerFeedbackSerializer,
)


class FeedbackRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["cycle", "subject", "reviewer", "status"]

    def get_serializer_class(self):
        if self.action == "create":
            return FeedbackRequestCreateSerializer
        return FeedbackRequestSerializer

    def get_queryset(self):
        user = self.request.user
        qs = FeedbackRequest.objects.select_related("subject", "reviewer").all()
        if user.role == "hr_admin":
            return qs
        return qs.filter(Q(subject=user) | Q(reviewer=user) | Q(requested_by=user))

    @action(detail=True, methods=["post"])
    def respond(self, request, pk=None):
        instance = self.get_object()
        if instance.reviewer_id != request.user.id:
            raise PermissionDenied("Only the assigned reviewer can respond to this request.")
        if instance.status != FeedbackRequest.Status.PENDING:
            raise ValidationError("This request has already been responded to.")
        serializer = FeedbackRequestRespondSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(FeedbackRequestSerializer(instance).data)


class PeerFeedbackViewSet(viewsets.ModelViewSet):
    """List/retrieve enforce BOTH the anonymity-threshold release gate and
    identity stripping (apps/feedback/permissions.py); submitting feedback
    (create) is always allowed for an accepted reviewer regardless of the
    release threshold, since the threshold only governs what is shown back
    to the subject/manager, not whether reviewers can submit."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return PeerFeedbackCreateSerializer
        return PeerFeedbackSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "hr_admin":
            return PeerFeedback.objects.select_related("reviewer", "subject").all()

        subject_id = self.request.query_params.get("subject")
        cycle_id = self.request.query_params.get("cycle")
        if subject_id and cycle_id:
            try:
                subject = User.objects.get(pk=subject_id)
            except User.DoesNotExist:
                return PeerFeedback.objects.none()
            is_self = subject_id == str(user.id)
            is_their_manager = subject.manager_id == user.id
            if not (is_self or is_their_manager):
                return PeerFeedback.objects.none()
            qs, released = visible_peer_feedback_for(user, subject, cycle_id)
            return qs if released else PeerFeedback.objects.none()

        # No subject/cycle filter given: reviewers can see feedback they
        # themselves authored (their own submission history).
        return PeerFeedback.objects.filter(reviewer=user)

    def perform_create(self, serializer):
        serializer.save()


class CalibrationSessionViewSet(viewsets.ModelViewSet):
    serializer_class = CalibrationSessionSerializer
    permission_classes = [IsHRAdmin]
    filterset_fields = ["cycle", "department"]
    queryset = CalibrationSession.objects.select_related("department").prefetch_related("entries").all()


class CalibrationEntryViewSet(viewsets.ModelViewSet):
    serializer_class = CalibrationEntrySerializer
    permission_classes = [IsHRAdmin]
    filterset_fields = ["session"]
    queryset = CalibrationEntry.objects.select_related("employee", "session").all()

    @action(detail=True, methods=["post"])
    def adjust(self, request, pk=None):
        instance = self.get_object()
        serializer = CalibrationEntryAdjustSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CalibrationEntrySerializer(instance).data)
