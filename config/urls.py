"""
URL configuration for the Campus Resource Hub API.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("accounts.urls")),
    path("api/resources/", include("resources.urls")),
    path("api/bookings/", include("bookings.urls")),
]
