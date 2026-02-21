from rest_framework import generics, views, status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
import datetime

from .serializers import (
    ResourceSerializer, ResourceCreateSerializer, ResourceUpdateSerializer,
    ResourceAdditionRequestSerializer, ResourceAdditionRequestReadSerializer,
    ResourceAdditionReviewSerializer, ResourceWeeklyScheduleSerializer,
    CalendarOverrideSerializer, AvailabilitySlotSerializer
)
from .models import Resource, ResourceAdditionRequest, ResourceWeeklySchedule, CalendarOverride
from apps.bookings.models import Booking
from apps.notifications.services import create_notification
from apps.audit.models import create_audit_log
from core.permissions import IsActiveAndApproved, IsAdmin, IsStaffRole, IsResourceManager
from core.response import success_response, error_response

class ResourceListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsActiveAndApproved(), IsAdmin()]
        return [IsAuthenticated(), IsActiveAndApproved()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResourceCreateSerializer
        return ResourceSerializer

    def get_queryset(self):
        queryset = Resource.objects.all()
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(location__icontains=search))
            
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter)
            
        min_capacity = self.request.query_params.get('min_capacity')
        if min_capacity:
            queryset = queryset.filter(capacity__gte=min_capacity)
            
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resource = serializer.save()

        # Auto-generate 7 weekly schedules
        schedules = []
        for day in range(7):
            is_working = True if day < 5 else False
            schedules.append(ResourceWeeklySchedule(
                resource=resource,
                day_of_week=day,
                start_time=datetime.time(8, 0),
                end_time=datetime.time(19, 0),
                is_working=is_working
            ))
        ResourceWeeklySchedule.objects.bulk_create(schedules)
        
        create_audit_log(
            actor=request.user,
            action="RESOURCE_CREATED",
            target_entity_type="resource",
            target_entity_id=resource.id,
            new_state=ResourceSerializer(resource).data,
            ip_address=getattr(request, 'audit_ip', None)
        )

        return success_response(ResourceSerializer(resource).data, status_code=status.HTTP_201_CREATED)

class ResourceDetailUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]
    queryset = Resource.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ResourceUpdateSerializer
        return ResourceSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def update(self, request, *args, **kwargs):
        resource = self.get_object()
        
        # Permission check
        if not (request.user.role == "ADMIN" or (request.user.role == "STAFF" and resource.managed_by == request.user)):
            return error_response(message="You do not have permission to edit this resource.", status_code=403)
            
        previous_state = ResourceSerializer(resource).data
        
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(resource, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        new_state = ResourceSerializer(resource).data
        
        create_audit_log(
            actor=request.user,
            action="RESOURCE_UPDATED",
            target_entity_type="resource",
            target_entity_id=resource.id,
            previous_state=previous_state,
            new_state=new_state,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        return success_response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != "ADMIN":
            return error_response(message="Only admins can delete resources.", status_code=403)
            
        resource = self.get_object()
        
        # Cancel bookings
        future_bookings = Booking.objects.filter(
            resource=resource,
            booking_date__gte=datetime.date.today(),
            status__in=["PENDING", "APPROVED"]
        )
        
        bookings_cancelled_count = 0
        for booking in future_bookings:
            booking.status = "CANCELLED"
            booking.cancellation_reason = "Resource removed by administrator"
            booking.cancelled_by = request.user
            booking.cancelled_at = timezone.now()
            booking.save()
            bookings_cancelled_count += 1
            
            create_notification(
                user=booking.user,
                message_type="BOOKING_AUTO_CANCELLED",
                title="Booking Auto-Cancelled",
                body=f"Your booking for {resource.name} on {booking.booking_date} has been cancelled because the resource was removed by administrator."
            )
            
            create_audit_log(
                actor=request.user,
                action="BOOKING_AUTO_CANCELLED",
                target_entity_type="booking",
                target_entity_id=booking.id,
                metadata={"reason": "Resource deleted"},
                ip_address=getattr(request, 'audit_ip', None)
            )

        create_audit_log(
            actor=request.user,
            action="RESOURCE_DELETED",
            target_entity_type="resource",
            target_entity_id=resource.id,
            metadata={"cancelled_bookings_count": bookings_cancelled_count},
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        resource.delete()
        return success_response(status_code=status.HTTP_204_NO_CONTENT)

class ResourceAdditionRequestCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsStaffRole]
    serializer_class = ResourceAdditionRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        req_obj = serializer.save(requested_by=request.user)
        
        create_audit_log(
            actor=request.user,
            action="RESOURCE_REQUEST_CREATED",
            target_entity_type="resource_request",
            target_entity_id=req_obj.id,
            new_state=ResourceAdditionRequestReadSerializer(req_obj).data,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        return success_response(ResourceAdditionRequestReadSerializer(req_obj).data, status_code=status.HTTP_201_CREATED)

class ResourceAdditionRequestListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]
    serializer_class = ResourceAdditionRequestReadSerializer

    def get_queryset(self):
        if self.request.user.role == "ADMIN":
            return ResourceAdditionRequest.objects.all().order_by('-created_at')
        elif self.request.user.role == "STAFF":
            return ResourceAdditionRequest.objects.filter(requested_by=self.request.user).order_by('-created_at')
        return ResourceAdditionRequest.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

class ApproveResourceRequestView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsAdmin]

    def post(self, request, pk):
        req_obj = get_object_or_404(ResourceAdditionRequest, pk=pk)
        
        if req_obj.status != "PENDING":
             return error_response(message="Request is not pending.", status_code=400)

        # Create the resource
        new_resource = Resource.objects.create(
            name=req_obj.proposed_name,
            type=req_obj.proposed_type,
            capacity=req_obj.proposed_capacity,
            total_quantity=req_obj.proposed_total_quantity,
            location=req_obj.proposed_location,
            description=req_obj.proposed_description,
            approval_type=req_obj.proposed_approval_type,
            managed_by=req_obj.requested_by 
        )
        
        # Auto-generate schedules
        schedules = []
        for day in range(7):
            is_working = True if day < 5 else False
            schedules.append(ResourceWeeklySchedule(
                resource=new_resource,
                day_of_week=day,
                start_time=datetime.time(8, 0),
                end_time=datetime.time(19, 0),
                is_working=is_working
            ))
        ResourceWeeklySchedule.objects.bulk_create(schedules)

        req_obj.status = "APPROVED"
        req_obj.reviewed_by = request.user
        req_obj.reviewed_at = timezone.now()
        req_obj.created_resource = new_resource
        req_obj.save()
        
        create_audit_log(
            actor=request.user,
            action="RESOURCE_REQUEST_APPROVED",
            target_entity_type="resource_request",
            target_entity_id=req_obj.id,
            metadata={"created_resource_id": new_resource.id},
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        create_notification(
            user=req_obj.requested_by,
            message_type="GENERAL", # Or specific type if added later
            title="Resource Request Approved",
            body=f"Your request to add resource '{new_resource.name}' has been approved."
        )
        
        return success_response(message="Resource request approved and resource created.")

class RejectResourceRequestView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsAdmin]

    def post(self, request, pk):
        req_obj = get_object_or_404(ResourceAdditionRequest, pk=pk)
        
        if req_obj.status != "PENDING":
             return error_response(message="Request is not pending.", status_code=400)

        serializer = ResourceAdditionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if serializer.validated_data['action'] != 'reject':
             return error_response(message="Invalid action.", status_code=400)

        req_obj.status = "REJECTED"
        req_obj.rejection_reason = serializer.validated_data.get('rejection_reason')
        req_obj.reviewed_by = request.user
        req_obj.reviewed_at = timezone.now()
        req_obj.save()
        
        create_audit_log(
            actor=request.user,
            action="RESOURCE_REQUEST_REJECTED",
            target_entity_type="resource_request",
            target_entity_id=req_obj.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        create_notification(
            user=req_obj.requested_by,
            message_type="GENERAL",
            title="Resource Request Rejected",
            body=f"Your request to add resource '{req_obj.proposed_name}' was rejected. Reason: {req_obj.rejection_reason}"
        )
        
        return success_response(message="Resource request rejected.")

class ResourceScheduleView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]

    def get(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        schedules = resource.weekly_schedules.all().order_by('day_of_week')
        data = ResourceWeeklyScheduleSerializer(schedules, many=True).data
        return success_response(data)

    def put(self, request, pk):
        if request.user.role != "ADMIN":
             return error_response(message="Only admins can update schedules.", status_code=403)
             
        resource = get_object_or_404(Resource, pk=pk)
        
        data = request.data
        if not isinstance(data, list) or len(data) != 7:
             return error_response(message="Expected a list of 7 schedule entries (0-6).", status_code=400)
             
        # Validate and update
        # Assuming input is list of dicts with day_of_week, start_time, end_time, is_working
        updated_schedules = []
        for entry in data:
            day = entry.get('day_of_week')
            if day is None or not (0 <= day <= 6):
                 return error_response(message="Invalid day_of_week.", status_code=400)
            
            schedule, created = ResourceWeeklySchedule.objects.update_or_create(
                resource=resource,
                day_of_week=day,
                defaults={
                    'start_time': entry.get('start_time', '08:00'),
                    'end_time': entry.get('end_time', '19:00'),
                    'is_working': entry.get('is_working', True)
                }
            )
            updated_schedules.append(schedule)
            
        create_audit_log(
            actor=request.user,
            action="SCHEDULE_UPDATED",
            target_entity_type="resource",
            target_entity_id=resource.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
            
        return success_response(ResourceWeeklyScheduleSerializer(updated_schedules, many=True).data)

class CalendarOverrideListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved] # GET open, POST limited
    serializer_class = CalendarOverrideSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsActiveAndApproved(), IsAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        return CalendarOverride.objects.all().order_by('override_date')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        override = serializer.save(created_by=request.user)
        
        create_audit_log(
            actor=request.user,
            action="CALENDAR_OVERRIDE_CREATED",
            target_entity_type="calendar_override",
            target_entity_id=override.id,
            new_state=CalendarOverrideSerializer(override).data,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        return success_response(CalendarOverrideSerializer(override).data, status_code=status.HTTP_201_CREATED)

class CalendarOverrideDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsAdmin]
    queryset = CalendarOverride.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        create_audit_log(
            actor=request.user,
            action="CALENDAR_OVERRIDE_DELETED",
            target_entity_type="calendar_override",
            target_entity_id=instance.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        instance.delete()
        return success_response(status_code=status.HTTP_204_NO_CONTENT)

class AvailabilityView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]

    def get(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        date_str = request.query_params.get('date')
        
        if not date_str:
             return error_response(message="date query parameter is required in YYYY-MM-DD format.", status_code=400)
             
        try:
            query_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
             return error_response(message="Invalid date format. Use YYYY-MM-DD.", status_code=400)

        # Determine if working day
        is_working_day = False
        start_time = datetime.time(8, 0)
        end_time = datetime.time(19, 0)
        
        override = CalendarOverride.objects.filter(override_date=query_date).first()
        if override:
            if override.override_type == "WORKING_DAY":
                is_working_day = True
            else: # HOLIDAY
                is_working_day = False
        else:
            # Check weekly schedule
            schedule = resource.weekly_schedules.filter(day_of_week=query_date.weekday()).first()
            if schedule and schedule.is_working:
                is_working_day = True
                start_time = schedule.start_time
                end_time = schedule.end_time

        slots = []
        if not is_working_day:
            # Generate slots but mark as NON_WORKING
            # Assuming standard hours if not working day, or empty? 
            # Instruction: "Generate potential slots (same hours) but mark all as status="NON_WORKING""
            # I'll use default 8-19 or the schedule's times if available, or just empty?
            # Let's use 8-19 default if no schedule
            pass
        
        # Generate hourly slots
        current_time = datetime.datetime.combine(query_date, start_time)
        end_datetime = datetime.datetime.combine(query_date, end_time)
        
        while current_time < end_datetime:
            slot_start = current_time.time()
            current_time += datetime.timedelta(hours=1)
            slot_end = current_time.time()
            if current_time > end_datetime:
                break
            
            slot_data = {
                "start_time": slot_start,
                "end_time": slot_end,
                "total_quantity": resource.total_quantity,
                "booked_quantity": 0,
                "available_quantity": 0,
                "status": "NON_WORKING"
            }
            
            if is_working_day:
                booked_qty = Booking.objects.filter(
                    resource=resource,
                    booking_date=query_date,
                    start_time=slot_start,
                    status__in=["PENDING", "APPROVED"]
                ).aggregate(total=Sum("quantity_requested"))["total"] or 0
                
                available = resource.total_quantity - booked_qty
                slot_data["booked_quantity"] = booked_qty
                slot_data["available_quantity"] = available
                slot_data["status"] = "AVAILABLE" if available > 0 else "FULLY_BOOKED"
            
            slots.append(slot_data)

        return success_response({
            "resource_id": resource.id,
            "date": date_str,
            "is_working_day": is_working_day,
            "slots": AccessibilitySlotSerializerWrapper(slots).data
        })

# Helper wrapper because AvailabilitySlotSerializer expects specific fields
# But I am serializing a list of dicts.
# I can just use AvailabilitySlotSerializer(many=True, data=slots) but that validates.
# I want to serialize outgoing data.
# Better to user AvailabilitySlotSerializer(slots, many=True) where slots are dicts (which DRF handles fine as objects access or dict access if setup, usually objects but dicts work if passed to serializer instance).
# Wait, ModelSerializer expects objects. Serializer expects data matching fields.
# AvailabilitySlotSerializer is a Serializer, not ModelSerializer.
# So I can pass the list of dicts as 'instance' to it.

class AccessibilitySlotSerializerWrapper:
    def __init__(self, data):
        self.data = AvailabilitySlotSerializer(data, many=True).data
