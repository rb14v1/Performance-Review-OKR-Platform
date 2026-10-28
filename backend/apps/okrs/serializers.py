from rest_framework import serializers

from apps.accounts.serializers import UserBriefSerializer
from apps.okrs.models import CheckIn, KeyResult, Objective
from apps.okrs.services import apply_check_in


class CheckInSerializer(serializers.ModelSerializer):
    created_by = UserBriefSerializer(read_only=True)

    class Meta:
        model = CheckIn
        fields = [
            "id",
            "key_result",
            "value",
            "confidence_level",
            "comment",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]

    def create(self, validated_data):
        request = self.context["request"]
        check_in = CheckIn.objects.create(created_by=request.user, **validated_data)
        apply_check_in(check_in)
        return check_in


class KeyResultSerializer(serializers.ModelSerializer):
    check_ins = CheckInSerializer(many=True, read_only=True)

    class Meta:
        model = KeyResult
        fields = [
            "id",
            "objective",
            "title",
            "metric_type",
            "start_value",
            "target_value",
            "current_value",
            "weight",
            "progress_pct",
            "check_ins",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "progress_pct", "created_at", "updated_at"]

    def create(self, validated_data):
        from apps.okrs.services import recalculate_key_result, recalculate_objective

        key_result = KeyResult.objects.create(**validated_data)
        recalculate_key_result(key_result)
        recalculate_objective(key_result.objective)
        return key_result


class ObjectiveListSerializer(serializers.ModelSerializer):
    owner = UserBriefSerializer(read_only=True)

    class Meta:
        model = Objective
        fields = [
            "id",
            "owner",
            "cycle",
            "parent_objective",
            "title",
            "description",
            "status",
            "progress_pct",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "progress_pct", "created_at", "updated_at"]


class ObjectiveDetailSerializer(ObjectiveListSerializer):
    key_results = KeyResultSerializer(many=True, read_only=True)
    child_objectives = ObjectiveListSerializer(many=True, read_only=True)

    class Meta(ObjectiveListSerializer.Meta):
        fields = ObjectiveListSerializer.Meta.fields + ["key_results", "child_objectives"]


class ObjectiveWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Objective
        fields = [
            "id",
            "cycle",
            "parent_objective",
            "title",
            "description",
            "status",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
