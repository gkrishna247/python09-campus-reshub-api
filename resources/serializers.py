from rest_framework import serializers

from .models import Resource


class ResourceSerializer(serializers.ModelSerializer):
    """Serializer for the Resource model."""

    class Meta:
        model = Resource
        fields = ["id", "name", "type", "capacity", "status"]
        read_only_fields = ["id"]

    def validate_capacity(self, value):
        """Ensure capacity is a positive integer."""
        if value <= 0:
            raise serializers.ValidationError("Capacity must be a positive integer.")
        return value
