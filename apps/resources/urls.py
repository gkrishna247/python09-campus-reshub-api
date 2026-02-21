from django.urls import path
from .views import (
    ResourceListCreateView, ResourceDetailUpdateDeleteView,
    ResourceAdditionRequestCreateView, ResourceAdditionRequestListView,
    ApproveResourceRequestView, RejectResourceRequestView,
    ResourceScheduleView, CalendarOverrideListCreateView, CalendarOverrideDeleteView,
    AvailabilityView
)

urlpatterns = [
    # Resources
    path("resources/", ResourceListCreateView.as_view(), name="resource-list-create"),
    path("resources/<int:pk>/", ResourceDetailUpdateDeleteView.as_view(), name="resource-detail"),
    path("resources/<int:pk>/schedule/", ResourceScheduleView.as_view(), name="resource-schedule"),
    path("resources/<int:pk>/availability/", AvailabilityView.as_view(), name="resource-availability"),
    
    # Resource Requests
    path("resource-requests/", ResourceAdditionRequestListView.as_view(), name="resource-request-list"),
    path("resource-requests/create/", ResourceAdditionRequestCreateView.as_view(), name="resource-request-create"),
    path("resource-requests/<int:pk>/approve/", ApproveResourceRequestView.as_view(), name="approve-resource-request"),
    path("resource-requests/<int:pk>/reject/", RejectResourceRequestView.as_view(), name="reject-resource-request"),
    
    # Calendar Overrides
    path("calendar-overrides/", CalendarOverrideListCreateView.as_view(), name="calendar-override-list"),
    path("calendar-overrides/<int:pk>/", CalendarOverrideDeleteView.as_view(), name="calendar-override-delete"),
]
