from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from core.mixins import SoftDeleteMixin, SoftDeleteManager
import datetime

class Resource(SoftDeleteMixin):
    TYPE_CHOICES = (
        ('LAB', 'Lab'),
        ('CLASSROOM', 'Classroom'),
        ('EVENT_HALL', 'Event Hall'),
    )
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('UNAVAILABLE', 'Unavailable'),
    )
    APPROVAL_TYPE_CHOICES = (
        ('AUTO_APPROVE', 'Auto Approve'),
        ('STAFF_APPROVE', 'Staff Approve'),
        ('ADMIN_APPROVE', 'Admin Approve'),
    )

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    capacity = models.IntegerField(default=0)
    total_quantity = models.IntegerField(default=1)
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    resource_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPE_CHOICES, default='AUTO_APPROVE')
    managed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='managed_resources')
    
    # SoftDeleteMixin provides is_deleted and deleted_at
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'resources'
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['resource_status']),
            models.Index(fields=['managed_by']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return self.name

class ResourceAdditionRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_addition_requests')
    proposed_name = models.CharField(max_length=200)
    proposed_type = models.CharField(max_length=20, choices=Resource.TYPE_CHOICES)
    proposed_capacity = models.IntegerField(default=0)
    proposed_total_quantity = models.IntegerField(default=1)
    proposed_location = models.CharField(max_length=255, blank=True, null=True)
    proposed_description = models.TextField(blank=True, null=True)
    proposed_approval_type = models.CharField(max_length=20, choices=Resource.APPROVAL_TYPE_CHOICES, default='AUTO_APPROVE')
    justification = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_resource_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_resource = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True, blank=True, related_name='addition_request')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resource_addition_requests'
        indexes = [
            models.Index(fields=['requested_by']),
            models.Index(fields=['status']),
        ]

class ResourceWeeklySchedule(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='weekly_schedules')
    day_of_week = models.SmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(6)])
    start_time = models.TimeField(default=datetime.time(8, 0))
    end_time = models.TimeField(default=datetime.time(19, 0))
    is_working = models.BooleanField(default=True)

    class Meta:
        db_table = 'resource_weekly_schedules'
        unique_together = [['resource', 'day_of_week']]
        indexes = [
            models.Index(fields=['resource']),
        ]

class CalendarOverride(models.Model):
    TYPE_CHOICES = (
        ('HOLIDAY', 'Holiday'),
        ('WORKING_DAY', 'Working Day'),
    )

    override_date = models.DateField(unique=True)
    override_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='calendar_overrides')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'calendar_overrides'
        indexes = [
            models.Index(fields=['created_by']),
        ]
