from rest_framework import serializers
from .models import AuditLog
from apps.accounts.serializers import UserMinimalSerializer

class AuditLogSerializer(serializers.ModelSerializer):
    actor = UserMinimalSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor', 'actor_email', 'action', 
            'target_entity_type', 'target_entity_id', 
            'previous_state', 'new_state', 'metadata', 
            'ip_address', 'timestamp'
        ]
        read_only_fields = fields
