from django.db import models
from apps.accounts.models import User

class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    actor_email = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=100, db_index=True)
    target_entity_type = models.CharField(max_length=50, db_index=True)
    target_entity_id = models.BigIntegerField(blank=True, null=True)
    previous_state = models.JSONField(blank=True, null=True)
    new_state = models.JSONField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['target_entity_type', 'target_entity_id']),
            models.Index(fields=['actor_email']),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("Audit logs cannot be modified")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Audit logs cannot be deleted")

    def __str__(self):
        return f"{self.action} by {self.actor_email} at {self.timestamp}"

def create_audit_log(actor, action, target_entity_type, target_entity_id=None, previous_state=None, new_state=None, metadata=None, ip_address=None):
    """
    Helper function to create an AuditLog entry.
    """
    actor_email = actor.email if actor else None
    
    # If actor is deleted or unavailable, we might still have the email
    # but here we just take it from the user object if present.
    
    return AuditLog.objects.create(
        actor=actor,
        actor_email=actor_email,
        action=action,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        previous_state=previous_state,
        new_state=new_state,
        metadata=metadata,
        ip_address=ip_address
    )
