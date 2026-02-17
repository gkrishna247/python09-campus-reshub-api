from rest_framework import serializers
from .models import Booking
from apps.accounts.serializers import UserMinimalSerializer
from apps.resources.models import Resource
from core.validators import validate_hourly_alignment
from django.utils import timezone
import datetime

class ResourceMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'name', 'type', 'location']

class BookingCreateSerializer(serializers.ModelSerializer):
    resource_id = serializers.IntegerField()
    start_time = serializers.TimeField(validators=[validate_hourly_alignment])

    class Meta:
        model = Booking
        fields = [
            'resource_id', 'booking_date', 'start_time', 
            'quantity_requested', 'is_special_request', 
            'special_request_reason'
        ]
        extra_kwargs = {
            'quantity_requested': {'default': 1, 'min_value': 1},
            'is_special_request': {'default': False},
            'special_request_reason': {'required': False, 'allow_blank': True}
        }

    def validate(self, data):
        if data.get('is_special_request') and not data.get('special_request_reason'):
            raise serializers.ValidationError({"special_request_reason": "Special request reason is required."})
        if data['booking_date'] < timezone.localdate():
             raise serializers.ValidationError({"booking_date": "Cannot book in the past."})
        return data

class BookingSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    resource = ResourceMinimalSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'resource', 'booking_date', 
            'start_time', 'end_time', 'quantity_requested', 
            'status', 'is_special_request', 'special_request_reason', 
            'cancellation_reason', 'cancelled_by', 'cancelled_at', 
            'approved_by', 'approved_at', 'rejected_by', 
            'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

class BookingApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({"rejection_reason": "Rejection reason is required."})
        return data

class BookingCancelSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField(required=True)

    def validate_cancellation_reason(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("Cancellation reason is required.")
        return value
