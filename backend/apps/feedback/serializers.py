from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import Department, User
from apps.accounts.serializers import DepartmentSerializer, UserBriefSerializer
from apps.feedback.models import (
    CalibrationEntry,
    CalibrationSession,
    FeedbackRequest,
    PeerFeedback,
)
from apps.feedback.permissions import is_hr_admin, serialize_identity


class FeedbackRequestSerializer(serializers.ModelSerializer):
    subject = UserBriefSerializer(read_only=True)
    reviewer = UserBriefSerializer(read_only=True)

    class Meta:
        model = FeedbackRequest
        fields = [
            "id",
            "cycle",
            "subject",
            "reviewer",
            "relationship",
            "status",
            "created_at",
            "responded_at",
        ]
        read_only_fields = ["id", "status", "created_at", "responded_at"]


class FeedbackRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackRequest
        fields = ["id", "cycle", "subject", "reviewer", "relationship"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        from apps.notifications.tasks import send_feedback_request_notification

        validated_data["requested_by"] = self.context["request"].user
        instance = super().create(validated_data)
        send_feedback_request_notification.delay(instance.id)
        return instance


class FeedbackRequestRespondSerializer(serializers.Serializer):
    accept = serializers.BooleanField()

    def save(self, **kwargs):
        instance = self.instance
        instance.status = (
            FeedbackRequest.Status.ACCEPTED
            if self.validated_data["accept"]
            else FeedbackRequest.Status.DECLINED
        )
        instance.responded_at = timezone.now()
        instance.save(update_fields=["status", "responded_at"])
        return instance


class PeerFeedbackSerializer(serializers.ModelSerializer):
    """Reviewer identity is stripped for anonymous entries unless the
    viewer is HR admin - see apps/feedback/permissions.serialize_identity.
    This is the single enforcement point used by every list/retrieve
    response so a subject or manager can never see a hidden reviewer field
    by requesting a different representation."""

    reviewer = serializers.SerializerMethodField()
    subject = UserBriefSerializer(read_only=True)

    class Meta:
        model = PeerFeedback
        fields = [
            "id",
            "cycle",
            "subject",
            "reviewer",
            "relationship",
            "anonymity_mode",
            "strengths",
            "improvements",
            "submitted_at",
        ]
        read_only_fields = fields

    def get_reviewer(self, obj):
        viewer = self.context["request"].user
        identity = serialize_identity(obj, viewer)
        return UserBriefSerializer(identity).data if identity else None


class PeerFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeerFeedback
        fields = [
            "id",
            "cycle",
            "subject",
            "relationship",
            "anonymity_mode",
            "strengths",
            "improvements",
            "feedback_request",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["reviewer"] = self.context["request"].user
        return super().create(validated_data)


class CalibrationEntrySerializer(serializers.ModelSerializer):
    employee = UserBriefSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(source="employee", queryset=User.objects.all())

    class Meta:
        model = CalibrationEntry
        fields = [
            "id",
            "session",
            "employee",
            "employee_id",
            "pre_rating",
            "post_rating",
            "adjustment_reason",
            "resolved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CalibrationEntryAdjustSerializer(serializers.Serializer):
    post_rating = serializers.CharField()
    adjustment_reason = serializers.CharField(required=False, allow_blank=True, default="")

    def save(self, **kwargs):
        instance = self.instance
        instance.post_rating = self.validated_data["post_rating"]
        instance.adjustment_reason = self.validated_data.get("adjustment_reason", "")
        instance.resolved = True
        instance.save(update_fields=["post_rating", "adjustment_reason", "resolved", "updated_at"])
        return instance


class CalibrationSessionSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(source="department", queryset=Department.objects.all())
    entries = CalibrationEntrySerializer(many=True, read_only=True)

    class Meta:
        model = CalibrationSession
        fields = [
            "id",
            "cycle",
            "department",
            "department_id",
            "facilitator",
            "status",
            "entries",
            "created_at",
        ]
        read_only_fields = ["id", "facilitator", "created_at"]

    def create(self, validated_data):
        validated_data["facilitator"] = self.context["request"].user
        return super().create(validated_data)
