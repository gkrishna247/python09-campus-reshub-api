from django.db import models
from django.core.validators import MinValueValidator
from apps.accounts.models import User
from apps.resources.models import Resource

class Booking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    quantity_requested = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_special_request = models.BooleanField(default=False)
    special_request_reason = models.TextField(blank=True, null=True)
    
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_bookings')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    rejected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_bookings')
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        indexes = [
            models.Index(fields=['resource', 'booking_date', 'start_time', 'status']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['booking_date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.resource.name} ({self.booking_date})"
