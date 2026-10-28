from rest_framework import serializers

from apps.accounts.models import Department, User


class UserBriefSerializer(serializers.ModelSerializer):
    """Minimal representation safe to nest inside other serializers."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role", "title"]
        read_only_fields = fields


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "parent_department", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    manager = UserBriefSerializer(read_only=True)
    manager_id = serializers.PrimaryKeyRelatedField(
        source="manager", queryset=User.objects.all(), write_only=True, required=False, allow_null=True
    )
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        source="department",
        queryset=Department.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "title",
            "manager",
            "manager_id",
            "department",
            "department_id",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "is_active", "date_joined"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "role",
            "title",
            "manager",
            "department",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
