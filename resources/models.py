from django.db import models


class Resource(models.Model):
    """Maps to the existing 'resources' table in campus_reshub_db."""

    TYPE_CHOICES = [
        ("LAB", "Lab"),
        ("CLASSROOM", "Classroom"),
        ("EVENT_HALL", "Event Hall"),
    ]

    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("UNAVAILABLE", "Unavailable"),
    ]

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default="AVAILABLE")

    class Meta:
        db_table = "resources"
        managed = False

    def __str__(self):
        return self.name
