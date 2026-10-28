from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.serializers import UserBriefSerializer
from apps.reviews.models import ManagerReview, Rating, ReviewCycle, SelfReview


class ReviewCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewCycle
        fields = ["id", "name", "start_date", "end_date", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class CycleTransitionSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=ReviewCycle.Status.choices)
    override_reason = serializers.CharField(required=False, allow_blank=True, default="")


class SelfReviewSerializer(serializers.ModelSerializer):
    employee = UserBriefSerializer(read_only=True)

    class Meta:
        model = SelfReview
        fields = [
            "id",
            "cycle",
            "employee",
            "accomplishments",
            "challenges",
            "self_rating",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "employee", "submitted_at", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["employee"] = self.context["request"].user
        return super().create(validated_data)


class SelfReviewSubmitSerializer(serializers.Serializer):
    def save(self, **kwargs):
        instance = self.instance
        instance.submitted_at = timezone.now()
        instance.save(update_fields=["submitted_at"])
        return instance


class ManagerReviewSerializer(serializers.ModelSerializer):
    employee = UserBriefSerializer(read_only=True)
    manager = UserBriefSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(source="employee", queryset=User.objects.all())

    class Meta:
        model = ManagerReview
        fields = [
            "id",
            "cycle",
            "employee",
            "employee_id",
            "manager",
            "manager_at_cycle_start",
            "draft_rating",
            "comments",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "employee",
            "manager",
            "manager_at_cycle_start",
            "submitted_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["manager"] = request.user
        # Snapshot the manager at the moment this review is created, so a
        # later reassignment of the employee never retroactively moves
        # historical review visibility.
        validated_data["manager_at_cycle_start"] = request.user
        return super().create(validated_data)


class ManagerReviewSubmitSerializer(serializers.Serializer):
    def save(self, **kwargs):
        instance = self.instance
        instance.submitted_at = timezone.now()
        instance.save(update_fields=["submitted_at"])
        return instance


class RatingSerializer(serializers.ModelSerializer):
    employee = UserBriefSerializer(read_only=True)

    class Meta:
        model = Rating
        fields = [
            "id",
            "cycle",
            "employee",
            "manager_at_cycle_start",
            "final_rating",
            "rating_source",
            "finalized_by",
            "finalized_at",
            "acknowledged_by_employee",
            "acknowledged_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "manager_at_cycle_start",
            "finalized_by",
            "finalized_at",
            "acknowledged_by_employee",
            "acknowledged_at",
            "created_at",
        ]


class RatingFinalizeSerializer(serializers.Serializer):
    final_rating = serializers.CharField()
    rating_source = serializers.ChoiceField(choices=Rating.Source.choices, default=Rating.Source.MANAGER)

    def save(self, **kwargs):
        instance = self.instance
        request = self.context["request"]
        instance.final_rating = self.validated_data["final_rating"]
        instance.rating_source = self.validated_data["rating_source"]
        instance.finalized_by = request.user
        instance.finalized_at = timezone.now()
        instance.save(
            update_fields=["final_rating", "rating_source", "finalized_by", "finalized_at"]
        )
        return instance


class RatingAcknowledgeSerializer(serializers.Serializer):
    def save(self, **kwargs):
        instance = self.instance
        instance.acknowledged_by_employee = True
        instance.acknowledged_at = timezone.now()
        instance.save(update_fields=["acknowledged_by_employee", "acknowledged_at"])
        return instance
