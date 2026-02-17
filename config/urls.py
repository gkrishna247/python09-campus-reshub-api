from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # API V1
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.resources.urls")),
    path("api/v1/", include("apps.bookings.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.audit.urls")),
    
    # Auth Token Refresh (Global) - also in accounts but good to have dedicated or reused
    # We put it in accounts urls as 'auth/token/refresh/' which is fine.
    
    # Schema & Documentation
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
