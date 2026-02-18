from django.urls import path
from .views import (
    BookingCreateView, BookingListView, AdminBookingListView,
    PendingBookingsView, ApproveBookingView, RejectBookingView,
    CancelBookingView
)

urlpatterns = [
    path("bookings/", BookingListView.as_view(), name="my-bookings"),
    path("bookings/create/", BookingCreateView.as_view(), name="booking-create"),
    path("bookings/all/", AdminBookingListView.as_view(), name="all-bookings"),
    path("bookings/pending/", PendingBookingsView.as_view(), name="pending-bookings"),
    path("bookings/<int:pk>/approve/", ApproveBookingView.as_view(), name="approve-booking"),
    path("bookings/<int:pk>/reject/", RejectBookingView.as_view(), name="reject-booking"),
    path("bookings/<int:pk>/cancel/", CancelBookingView.as_view(), name="cancel-booking"),
]
