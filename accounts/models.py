from django.db import models


class User(models.Model):
    """Maps to the existing 'users' table in campus_reshub_db."""

    ROLE_CHOICES = [
        ("STUDENT", "Student"),
        ("STAFF", "Staff"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True, default=None)
    role = models.CharField(max_length=7, choices=ROLE_CHOICES, default="STUDENT")
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"
        managed = False

    def __str__(self):
        return self.name
