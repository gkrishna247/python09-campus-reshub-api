from rest_framework import serializers
from .models import UserNotification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = [
            'id', 'user', 'message_type', 'title', 'body', 
            'related_entity_type', 'related_entity_id', 
            'is_read', 'is_email_sent', 'created_at'
        ]
        read_only_fields = fields
