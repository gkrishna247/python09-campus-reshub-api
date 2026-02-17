from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""

    class Meta:
        model = User
        fields = ["id", "name", "email", "phone", "role", "status", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_email(self, value):
        """Ensure email uniqueness on create and update."""
        request = self.context.get("request")
        queryset = User.objects.filter(email=value)

        # On update, exclude the current instance
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("A user with this email already exists.")

        return value
