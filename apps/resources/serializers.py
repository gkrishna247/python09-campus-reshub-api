from rest_framework import serializers
from .models import Resource, ResourceAdditionRequest, ResourceWeeklySchedule, CalendarOverride
from apps.accounts.serializers import UserMinimalSerializer
from apps.accounts.models import User
from django.db.models import Q

class ResourceWeeklyScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = ResourceWeeklySchedule
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time', 'is_working']
        read_only_fields = ['id']

    def get_day_name(self, obj):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if 0 <= obj.day_of_week <= 6:
            return days[obj.day_of_week]
        return "Unknown"

class ResourceSerializer(serializers.ModelSerializer):
    managed_by = UserMinimalSerializer(read_only=True)
    weekly_schedules = ResourceWeeklyScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Resource
        fields = [
            'id', 'name', 'type', 'capacity', 'total_quantity', 
            'location', 'description', 'resource_status', 
            'approval_type', 'managed_by', 'weekly_schedules',
            'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_deleted', 'weekly_schedules']

class ResourceCreateSerializer(serializers.ModelSerializer):
    managed_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='STAFF'),
        required=True
    )

    class Meta:
        model = Resource
        fields = [
            'name', 'type', 'capacity', 'total_quantity', 
            'location', 'description', 'resource_status', 
            'approval_type', 'managed_by'
        ]

    def validate_managed_by(self, value):
        if value.role != 'STAFF':
            raise serializers.ValidationError("Managed by user must have STAFF role.")
        return value

class ResourceUpdateSerializer(serializers.ModelSerializer):
    managed_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='STAFF'),
        required=False
    )
    
    class Meta:
        model = Resource
        fields = [
            'name', 'type', 'capacity', 'total_quantity', 
            'location', 'description', 'resource_status', 
            'approval_type', 'managed_by'
        ]
        extra_kwargs = {
            'name': {'required': False},
            'type': {'required': False},
            # all optional by default with partial=True in view
        }

    def validate_managed_by(self, value):
        if value and value.role != 'STAFF':
            raise serializers.ValidationError("Managed by user must have STAFF role.")
        return value

class ResourceAdditionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceAdditionRequest
        fields = [
            'proposed_name', 'proposed_type', 'proposed_capacity', 
            'proposed_total_quantity', 'proposed_location', 
            'proposed_description', 'proposed_approval_type', 
            'justification'
        ]

    def validate_justification(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("Justification is required.")
        return value

class ResourceAdditionRequestReadSerializer(serializers.ModelSerializer):
    requested_by = UserMinimalSerializer(read_only=True)
    reviewed_by = UserMinimalSerializer(read_only=True)
    created_resource = ResourceSerializer(read_only=True)

    class Meta:
        model = ResourceAdditionRequest
        fields = [
            'id', 'requested_by', 'proposed_name', 'proposed_type', 
            'proposed_capacity', 'proposed_total_quantity', 
            'proposed_location', 'proposed_description', 
            'proposed_approval_type', 'justification', 
            'status', 'rejection_reason', 'reviewed_by', 
            'reviewed_at', 'created_resource', 'created_at'
        ]
        read_only_fields = fields

class ResourceAdditionReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({"rejection_reason": "Rejection reason is required."})
        return data

class CalendarOverrideSerializer(serializers.ModelSerializer):
    created_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = CalendarOverride
        fields = ['id', 'override_date', 'override_type', 'description', 'created_by']
        read_only_fields = ['id', 'created_by']

class AvailabilitySlotSerializer(serializers.Serializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    total_quantity = serializers.IntegerField()
    booked_quantity = serializers.IntegerField()
    available_quantity = serializers.IntegerField()
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        # obj is a dict here from the view logic
        if obj.get('is_working_day', True) is False:
             return "NON_WORKING"
        if obj['available_quantity'] > 0:
            return "AVAILABLE"
        return "FULLY_BOOKED"
