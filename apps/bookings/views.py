from rest_framework import generics, views, status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
import datetime

from .serializers import (
    BookingSerializer, BookingCreateSerializer, BookingApprovalSerializer,
    BookingCancelSerializer
)
from .models import Booking
from apps.resources.models import Resource, CalendarOverride, ResourceWeeklySchedule
from apps.notifications.services import create_notification, notify_admins, notify_faculty
from apps.audit.models import create_audit_log
from core.permissions import IsActiveAndApproved, IsAdmin, CanBook
from core.response import success_response, error_response

class BookingCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, CanBook]
    serializer_class = BookingCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        resource_id = serializer.validated_data['resource_id']
        booking_date = serializer.validated_data['booking_date']
        start_time = serializer.validated_data['start_time']
        quantity = serializer.validated_data['quantity_requested']
        is_special = serializer.validated_data['is_special_request']
        reason = serializer.validated_data.get('special_request_reason')

        # Resource verification
        resource = get_object_or_404(Resource, pk=resource_id)
        if resource.is_deleted or resource.resource_status != "AVAILABLE":
             return error_response(message="Resource is not available.", status_code=400)

        # Time calculation
        # start_time is validated hourly (00 min 00 sec)
        # combine date and time
        start_dt = datetime.datetime.combine(booking_date, start_time)
        end_dt = start_dt + datetime.timedelta(hours=1)
        end_time = end_dt.time()
        
        # Working day verification
        is_working = False
        override = CalendarOverride.objects.filter(override_date=booking_date).first()
        
        if override:
            if override.override_type == "WORKING_DAY":
                is_working = True
            elif override.override_type == "HOLIDAY" and not is_special:
                 return error_response(message="Cannot book on a non-working day. Submit a special request instead.", status_code=400)
        else:
            schedule = resource.weekly_schedules.filter(day_of_week=booking_date.weekday()).first()
            if schedule and schedule.is_working:
                is_working = True
            elif not is_special:
                 return error_response(message="Cannot book on a non-working day. Submit a special request instead.", status_code=400)
                 
        if is_special and not reason:
             return error_response(message="Special request reason is required.", status_code=400)
             
        # Concurrency safe booking
        with transaction.atomic():
            # Lock the resource record (or checking capacity aggregation while locking booking table rows for this slot? 
            # Locking resource is safer/simpler to serialize checks on this resource)
            # But we are aggregating from Booking table.
            # Best is to select_for_update on Resource to serialize all bookings for it.
            resource_locked = Resource.objects.select_for_update().get(pk=resource.pk)
            
            booked_qty = Booking.objects.filter(
                resource=resource_locked,
                booking_date=booking_date,
                start_time=start_time,
                status__in=["PENDING", "APPROVED"]
            ).aggregate(total=Sum("quantity_requested"))["total"] or 0
            
            if booked_qty + quantity > resource_locked.total_quantity:
                 return error_response(message="Insufficient availability for the requested slot.", status_code=409)

            # Determine initial status
            status_val = "PENDING"
            approved_by = None
            approved_at = None
            
            if resource_locked.approval_type == "AUTO_APPROVE":
                status_val = "APPROVED"
                approved_by = request.user # System auto-approve but user initiated? Or None?
                # User requested so authorized by system logic.
                # Instructions: "approved_by=request.user if status=='APPROVED' else None"
                approved_by = request.user
                approved_at = timezone.now()
            
            booking = Booking.objects.create(
                user=request.user,
                resource=resource_locked,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                quantity_requested=quantity,
                status=status_val,
                is_special_request=is_special,
                special_request_reason=reason,
                approved_by=approved_by,
                approved_at=approved_at
            )
            
        # Post-transaction: Notifications & Audit
        create_audit_log(
            actor=request.user,
            action="BOOKING_CREATED",
            target_entity_type="booking",
            target_entity_id=booking.id,
            new_state=BookingSerializer(booking).data,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        if status_val == "APPROVED":
            create_notification(
                user=request.user,
                message_type="BOOKING_APPROVED",
                title="Booking Approved",
                body=f"Your booking for {resource.name} on {booking_date} has been auto-approved."
            )
        else:
            # Notify approver
            title = "New Booking Request"
            body = f"User {request.user.name} requested {resource.name} on {booking_date}."
            if resource.approval_type == "STAFF_APPROVE":
                # Notify manager
                create_notification(
                    user=resource.managed_by,
                    message_type="GENERAL", # Or specific type for request
                    title=title,
                    body=body
                )
            elif resource.approval_type == "ADMIN_APPROVE":
                notify_admins("GENERAL", title, body)
                
        return success_response(BookingSerializer(booking).data, status_code=status.HTTP_201_CREATED)

class BookingListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved] # CanBook implied by being authenticated? No, admins can view too.
    serializer_class = BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user, 
            booking_date__gte=datetime.date.today(),
            status__in=["PENDING", "APPROVED"]
        ).order_by("booking_date", "start_time")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

class AdminBookingListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsAdmin]
    serializer_class = BookingSerializer

    def get_queryset(self):
        queryset = Booking.objects.all()
        
        resource_id = self.request.query_params.get('resource_id')
        if resource_id:
            queryset = queryset.filter(resource__id=resource_id)
            
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user__id=user_id)
            
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        date_from = self.request.query_params.get('date_from')
        if date_from:
             queryset = queryset.filter(booking_date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
             queryset = queryset.filter(booking_date__lte=date_to)

        return queryset.order_by("-booking_date")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

class PendingBookingsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]
    serializer_class = BookingSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return Booking.objects.filter(status="PENDING")
        elif user.role == "STAFF":
            return Booking.objects.filter(
                status="PENDING",
                resource__managed_by=user,
                resource__approval_type="STAFF_APPROVE"
            )
        else:
            return Booking.objects.none()
            
    def list(self, request, *args, **kwargs):
        if request.user.role not in ["ADMIN", "STAFF"]:
             return error_response(message="Permission denied.", status_code=403)
             
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

class ApproveBookingView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        
        if booking.status != "PENDING":
             return error_response(message="Only pending bookings can be approved.", status_code=400)
             
        resource = booking.resource
        
        # Auth check
        if resource.approval_type == "AUTO_APPROVE":
             return error_response(message="Auto-approved resources do not require manual approval.", status_code=400)
             
        if resource.approval_type == "STAFF_APPROVE":
            if resource.managed_by != request.user:
                 return error_response(message="Only the resource manager can approve this.", status_code=403)
        
        if resource.approval_type == "ADMIN_APPROVE":
             if request.user.role != "ADMIN":
                 return error_response(message="Only admins can approve this.", status_code=403)

        booking.status = "APPROVED"
        booking.approved_by = request.user
        booking.approved_at = timezone.now()
        booking.save()
        
        create_audit_log(
            actor=request.user,
            action="BOOKING_APPROVED",
            target_entity_type="booking",
            target_entity_id=booking.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        create_notification(
            user=booking.user,
            message_type="BOOKING_APPROVED",
            title="Booking Approved",
            body=f"Your booking for {resource.name} on {booking.booking_date} {booking.start_time}-{booking.end_time} has been approved."
        )
        
        return success_response(message="Booking approved.")

class RejectBookingView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        
        if booking.status != "PENDING":
             return error_response(message="Only pending bookings can be rejected.", status_code=400)

        resource = booking.resource
        
        # Auth check (same as approve)
        if resource.approval_type == "STAFF_APPROVE":
            if resource.managed_by != request.user:
                 return error_response(message="Only the resource manager can reject this.", status_code=403)
        if resource.approval_type == "ADMIN_APPROVE":
             if request.user.role != "ADMIN":
                 return error_response(message="Only admins can reject this.", status_code=403)
                 
        serializer = BookingApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if serializer.validated_data['action'] != 'reject':
             return error_response(message="Invalid action.", status_code=400)

        booking.status = "REJECTED"
        booking.rejected_by = request.user
        booking.rejection_reason = serializer.validated_data.get('rejection_reason')
        booking.save()
        
        create_audit_log(
            actor=request.user,
            action="BOOKING_REJECTED",
            target_entity_type="booking",
            target_entity_id=booking.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        create_notification(
            user=booking.user,
            message_type="BOOKING_REJECTED",
            title="Booking Rejected",
            body=f"Your booking for {resource.name} on {booking.booking_date} was rejected. Reason: {booking.rejection_reason}"
        )
        
        return success_response(message="Booking rejected.")

class CancelBookingView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        
        if booking.status in ["CANCELLED", "REJECTED"]:
             return error_response(message="This booking cannot be cancelled.", status_code=400)
             
        # Auth check
        if not (booking.user == request.user or request.user.role == "ADMIN"):
             return error_response(message="Permission denied.", status_code=403)
             
        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        previous_status = booking.status
        booking.status = "CANCELLED"
        booking.cancellation_reason = serializer.validated_data['cancellation_reason']
        booking.cancelled_by = request.user
        booking.cancelled_at = timezone.now()
        booking.save()
        
        create_audit_log(
            actor=request.user,
            action="BOOKING_CANCELLED",
            target_entity_type="booking",
            target_entity_id=booking.id,
            previous_state={"status": previous_status},
            new_state={"status": "CANCELLED"},
            metadata={"reason": booking.cancellation_reason},
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        create_notification(
            user=booking.user,
            message_type="BOOKING_CANCELLED",
            title="Booking Cancelled",
            body=f"Booking for {booking.resource.name} on {booking.booking_date} cancelled. Reason: {booking.cancellation_reason}"
        )
        
        return success_response(message="Booking cancelled.")
