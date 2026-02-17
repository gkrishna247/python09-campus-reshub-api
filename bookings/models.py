from django.db import models

from accounts.models import User
from resources.models import Resource


class Booking(models.Model):
    """Maps to the existing 'bookings' table in campus_reshub_db."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
    )
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        db_column="resource_id",
    )
    booking_date = models.DateField()
    time_slot = models.CharField(max_length=50)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default="PENDING")

    class Meta:
        db_table = "bookings"
        managed = False
        unique_together = [("resource", "booking_date", "time_slot")]

    def __str__(self):
        return f"Booking #{self.id} - {self.user} - {self.resource}"
