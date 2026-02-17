from django.db import models
from apps.accounts.models import User

class UserNotification(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('BOOKING_APPROVED', 'Booking Approved'),
        ('BOOKING_REJECTED', 'Booking Rejected'),
        ('BOOKING_CANCELLED', 'Booking Cancelled'),
        ('BOOKING_AUTO_CANCELLED', 'Booking Auto Cancelled'),
        ('REGISTRATION_APPROVED', 'Registration Approved'),
        ('REGISTRATION_REJECTED', 'Registration Rejected'),
        ('ROLE_CHANGE_APPROVED', 'Role Change Approved'),
        ('ROLE_CHANGE_REJECTED', 'Role Change Rejected'),
        ('GENERAL', 'General'),
    )

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message_type = models.CharField(max_length=30, choices=MESSAGE_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    related_entity_type = models.CharField(max_length=50, blank=True, null=True)
    related_entity_id = models.BigIntegerField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['message_type']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"
