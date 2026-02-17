from rest_framework import serializers

from accounts.models import User
from accounts.serializers import UserSerializer
from resources.models import Resource
from resources.serializers import ResourceSerializer
from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Booking model.

    Read operations: nested full UserSerializer and ResourceSerializer.
    Write operations: accept user_id and resource_id as integers.
    """

    # Nested serializers for read (output)
    user = UserSerializer(read_only=True)
    resource = ResourceSerializer(read_only=True)

    # Write-only fields for create/update
    user_id = serializers.IntegerField(write_only=True)
    resource_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "resource",
            "user_id",
            "resource_id",
            "booking_date",
            "time_slot",
            "status",
        ]
        read_only_fields = ["id"]

    def validate_user_id(self, value):
        """Validate that the user exists."""
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                "User with this ID does not exist."
            )
        return value

    def validate_resource_id(self, value):
        """Validate that the resource exists."""
        if not Resource.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                "Resource with this ID does not exist."
            )
        return value

    def create(self, validated_data):
        """Create booking using user_id and resource_id."""
        user_id = validated_data.pop("user_id")
        resource_id = validated_data.pop("resource_id")
        validated_data["user"] = User.objects.get(pk=user_id)
        validated_data["resource"] = Resource.objects.get(pk=resource_id)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update booking, resolving user_id and resource_id if provided."""
        if "user_id" in validated_data:
            user_id = validated_data.pop("user_id")
            validated_data["user"] = User.objects.get(pk=user_id)
        if "resource_id" in validated_data:
            resource_id = validated_data.pop("resource_id")
            validated_data["resource"] = Resource.objects.get(pk=resource_id)
        return super().update(instance, validated_data)
