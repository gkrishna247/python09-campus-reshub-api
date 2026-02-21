from rest_framework import generics, views, status, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import datetime

from .serializers import (
    RegisterSerializer, CustomTokenObtainPairSerializer, UserSerializer, 
    UserUpdateSerializer, ProfileSerializer, ChangePasswordSerializer,
    RegistrationApprovalSerializer, RoleChangeRequestCreateSerializer,
    RoleChangeRequestSerializer, RoleChangeReviewSerializer
)
from .models import RoleChangeRequest
from apps.audit.models import create_audit_log
from apps.notifications.services import create_notification, notify_admins, notify_faculty
from apps.resources.models import Resource, ResourceAdditionRequest
from apps.bookings.models import Booking
from core.permissions import IsActiveAndApproved, IsAdmin, IsFacultyOrAdmin
from core.response import success_response, error_response

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Audit Log
        create_audit_log(
            actor=None,
            action="USER_REGISTERED",
            target_entity_type="user",
            target_entity_id=user.id,
            new_state={"email": user.email, "role": user.role},
            ip_address=getattr(request, 'audit_ip', None)
        )

        # Notify approvers
        if user.approval_status == "PENDING":
            title = "New User Registration"
            body = f"User {user.name} ({user.email}) has registered and requires approval."
            if user.role == "STUDENT":
                notify_faculty("NEW_REGISTRATION", title, body, "user", user.id)
            else:
                notify_admins("NEW_REGISTRATION", title, body, "user", user.id)

        return success_response({
            "user": serializer.data,
            "approval_status": user.approval_status
        }, message="Registration successful.", status_code=status.HTTP_201_CREATED)

class LoginView(TokenObtainPairView):
    # Serializer class set in settings but good to be explicit
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_401_UNAUTHORIZED)
            
        # Get user from validated data
        # CustomTokenObtainPairSerializer puts user data in 'user' key of validated_data
        # but self.user is available on serializer instance after validation if we access it correctly
        # Actually TokenObtainPairSerializer doesn't set self.user publicly easily, 
        # but our custom validate() returns a dict with 'user'.
        
        # To get the user object for audit log:
        user_email = request.data.get(User.USERNAME_FIELD)
        user = User.objects.filter(email=user_email).first()

        if user:
            create_audit_log(
                actor=user,
                action="USER_LOGIN",
                target_entity_type="user",
                target_entity_id=user.id,
                ip_address=getattr(request, 'audit_ip', None)
            )

        return success_response(serializer.validated_data, message="Login successful.")

class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return error_response(message="Refresh token is required.")
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            create_audit_log(
                actor=request.user,
                action="USER_LOGOUT",
                target_entity_type="user",
                target_entity_id=request.user.id,
                ip_address=getattr(request, 'audit_ip', None)
            )
            
            return success_response(message="Logout successful.")
        except Exception as e:
            return error_response(message=str(e))

class ApprovalStatusView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "email": request.user.email,
            "name": request.user.name,
            "role": request.user.role,
            "approval_status": request.user.approval_status,
            "rejection_reason": request.user.rejection_reason
        }
        return success_response(data)

class UserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsAdmin]
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = User.objects.all()
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(account_status=status_filter)
            
        role_filter = self.request.query_params.get('role')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
            
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(email__icontains=search))
            
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsAdmin]
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        previous_state = UserSerializer(instance).data
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        new_state = UserSerializer(instance).data
        
        create_audit_log(
            actor=request.user,
            action="USER_UPDATED",
            target_entity_type="user",
            target_entity_id=instance.id,
            previous_state=previous_state,
            new_state=new_state,
            ip_address=getattr(request, 'audit_ip', None)
        )

        return success_response(serializer.data, message="User updated successfully.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        create_audit_log(
            actor=request.user,
            action="USER_DELETED",
            target_entity_type="user",
            target_entity_id=instance.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        instance.delete() # Soft delete
        return success_response(status_code=status.HTTP_204_NO_CONTENT)

class ProfileView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.approval_status == "APPROVED":
            serializer = ProfileSerializer(request.user)
        else:
            # Minimal data
            data = {
                "id": request.user.id,
                "email": request.user.email,
                "name": request.user.name,
                "role": request.user.role,
                "account_status": request.user.account_status,
                "approval_status": request.user.approval_status,
                "rejection_reason": request.user.rejection_reason
            }
            return success_response(data)
            
        return success_response(serializer.data)
        
    def patch(self, request):
        if not IsActiveAndApproved().has_permission(request, self):
            return error_response(message="Account inactive or unapproved.", status_code=403)

        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        create_audit_log(
            actor=request.user,
            action="PROFILE_UPDATED",
            target_entity_type="user",
            target_entity_id=request.user.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        return success_response(serializer.data, message="Profile updated.")

class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        create_audit_log(
            actor=request.user,
            action="PASSWORD_CHANGED",
            target_entity_type="user",
            target_entity_id=user.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        return success_response(message="Password changed successfully.")

class PendingRegistrationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsFacultyOrAdmin]
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = User.objects.filter(approval_status="PENDING")
        if self.request.user.role == "FACULTY":
            queryset = queryset.filter(role="STUDENT")
        # Admin sees all pending
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

class ApproveRegistrationView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsFacultyOrAdmin]

    def post(self, request, pk):
        user_to_approve = get_object_or_404(User, pk=pk)
        
        # Check permissions
        if request.user.role == "FACULTY" and user_to_approve.role != "STUDENT":
            return error_response(message="Faculty can only approve students.", status_code=403)
            
        user_to_approve.approval_status = "APPROVED"
        user_to_approve.save()
        
        create_audit_log(
            actor=request.user,
            action="REGISTRATION_APPROVED",
            target_entity_type="user",
            target_entity_id=user_to_approve.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        create_notification(
            user=user_to_approve,
            message_type="REGISTRATION_APPROVED",
            title="Registration Approved",
            body="Your registration has been approved. You can now access the system."
        )
        
        return success_response(message="User approved successfully.")

class RejectRegistrationView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsFacultyOrAdmin]

    def post(self, request, pk):
        user_to_reject = get_object_or_404(User, pk=pk)
        
        # Check permissions
        if request.user.role == "FACULTY" and user_to_reject.role != "STUDENT":
            return error_response(message="Faculty can only reject students.", status_code=403)
            
        serializer = RegistrationApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if serializer.validated_data['action'] != 'reject':
             return error_response(message="Invalid action.", status_code=400)

        user_to_reject.approval_status = "REJECTED"
        user_to_reject.rejection_reason = serializer.validated_data.get('rejection_reason')
        user_to_reject.save()
        
        create_audit_log(
            actor=request.user,
            action="REGISTRATION_REJECTED",
            target_entity_type="user",
            target_entity_id=user_to_reject.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        create_notification(
            user=user_to_reject,
            message_type="REGISTRATION_REJECTED",
            title="Registration Rejected",
            body=f"Your registration was rejected. Reason: {user_to_reject.rejection_reason}"
        )
        
        return success_response(message="User rejected successfully.")

class RoleChangeRequestCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]
    serializer_class = RoleChangeRequestCreateSerializer

    def post(self, request, *args, **kwargs):
        if request.user.role == "ADMIN":
            return error_response(message="Admins cannot request role changes.", status_code=403)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        role_request = RoleChangeRequest.objects.create(
            user=request.user,
            current_role=request.user.role,
            requested_role=serializer.validated_data['requested_role']
        )
        
        create_audit_log(
            actor=request.user,
            action="ROLE_CHANGE_REQUESTED",
            target_entity_type="role_change_request",
            target_entity_id=role_request.id,
            ip_address=getattr(request, 'audit_ip', None)
        )

        title = "Role Change Request"
        body = f"User {request.user.name} requests change to {role_request.requested_role}."
        if role_request.requested_role == "STUDENT":
            notify_faculty("ROLE_CHANGE_REQUESTED", title, body, "role_change", role_request.id)
        else:
            notify_admins("ROLE_CHANGE_REQUESTED", title, body, "role_change", role_request.id)

        return success_response(data=RoleChangeRequestSerializer(role_request).data, status_code=201)

class RoleChangeRequestListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsFacultyOrAdmin]
    serializer_class = RoleChangeRequestSerializer

    def get_queryset(self):
        queryset = RoleChangeRequest.objects.filter(status="PENDING")
        if self.request.user.role == "FACULTY":
            queryset = queryset.filter(requested_role="STUDENT")
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

class MyRoleChangeRequestsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]
    serializer_class = RoleChangeRequestSerializer

    def get_queryset(self):
        return RoleChangeRequest.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

class ApproveRoleChangeView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsFacultyOrAdmin]

    def post(self, request, pk):
        role_request = get_object_or_404(RoleChangeRequest, pk=pk)
        
        if role_request.status != "PENDING":
             return error_response(message="Request is not pending.", status_code=400)

        # Permissions
        if role_request.requested_role == "STUDENT":
             # Faculty or Admin ok
             pass
        elif role_request.requested_role in ["FACULTY", "STAFF"]:
             if request.user.role != "ADMIN":
                 return error_response(message="Only Admin can approve changes to Faculty/Staff.", status_code=403)
        
        role_request.status = "APPROVED"
        role_request.reviewed_by = request.user
        role_request.reviewed_at = timezone.now()
        role_request.save()
        
        user = role_request.user
        previous_role = user.role
        user.role = role_request.requested_role
        user.save()
        
        create_audit_log(
            actor=request.user,
            action="ROLE_CHANGE_APPROVED",
            target_entity_type="user",
            target_entity_id=user.id,
            previous_state={"role": previous_role},
            new_state={"role": user.role},
            metadata={"request_id": role_request.id},
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        create_notification(
            user=user,
            message_type="ROLE_CHANGE_APPROVED",
            title="Role Change Approved",
            body=f"Your role has been changed to {user.role}."
        )
        
        return success_response(message="Role change approved.")

class RejectRoleChangeView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsFacultyOrAdmin]

    def post(self, request, pk):
        role_request = get_object_or_404(RoleChangeRequest, pk=pk)

        if role_request.status != "PENDING":
             return error_response(message="Request is not pending.", status_code=400)

        # Check permissions (same as approve)
        if role_request.requested_role == "STUDENT":
             pass
        elif role_request.requested_role in ["FACULTY", "STAFF"]:
             if request.user.role != "ADMIN":
                 return error_response(message="Only Admin can reject changes to Faculty/Staff.", status_code=403)
        
        serializer = RoleChangeReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if serializer.validated_data['action'] != 'reject':
             return error_response(message="Invalid action.", status_code=400)

        role_request.status = "REJECTED"
        role_request.rejection_reason = serializer.validated_data.get('rejection_reason')
        role_request.reviewed_by = request.user
        role_request.reviewed_at = timezone.now()
        role_request.save()
        
        create_audit_log(
            actor=request.user,
            action="ROLE_CHANGE_REJECTED",
            target_entity_type="role_change_request",
            target_entity_id=role_request.id,
            ip_address=getattr(request, 'audit_ip', None)
        )
        
        create_notification(
            user=role_request.user,
            message_type="ROLE_CHANGE_REJECTED",
            title="Role Change Rejected",
            body=f"Your role change request to {role_request.requested_role} was rejected. Reason: {role_request.rejection_reason}"
        )
        
        return success_response(message="Role change rejected.")

class StatisticsView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsAdmin]

    def get(self, request):
        range_param = request.query_params.get('range', 'THIS_WEEK')
        today = timezone.now().date()
        
        if range_param == 'TODAY':
            start_date = today
        elif range_param == 'THIS_WEEK':
            start_date = today - timedelta(days=today.weekday())
        elif range_param == 'THIS_MONTH':
            start_date = today.replace(day=1)
        # ALL_TIME default logic handled by not filtering date if not set or just filtering everything
        else:
             start_date = None # ALL_TIME

        # Users
        total_users = User.objects.count()
        users_by_role = User.objects.values('role').annotate(count=Count('id'))
        active_users = User.objects.filter(account_status="ACTIVE").count()
        inactive_users = User.objects.filter(account_status="INACTIVE").count()
        
        # Resources
        total_resources = Resource.objects.count()
        resources_by_type = Resource.objects.values('type').annotate(count=Count('id'))

        # Bookings
        bookings_query = Booking.objects.all()
        if start_date:
            bookings_query = bookings_query.filter(created_at__date__gte=start_date)
            
        total_bookings = bookings_query.count()
        bookings_status = bookings_query.values('status').annotate(count=Count('id'))
        
        # Pending Approvals
        pending_registrations = User.objects.filter(approval_status="PENDING").count()
        pending_bookings = Booking.objects.filter(status="PENDING").count()
        pending_resource_requests = ResourceAdditionRequest.objects.filter(status="PENDING").count()
        pending_role_changes = RoleChangeRequest.objects.filter(status="PENDING").count()
        
        # Most booked resources
        most_booked = Booking.objects.filter(
            created_at__date__gte=start_date if start_date else datetime.date(2000, 1, 1)
        ).values('resource__id', 'resource__name').annotate(count=Count('id')).order_by('-count')[:5]

        data = {
            "users": {
                "total": total_users,
                "by_role": list(users_by_role),
                "active": active_users,
                "inactive": inactive_users
            },
            "resources": {
                "total": total_resources,
                "by_type": list(resources_by_type)
            },
            "bookings": {
                "total": total_bookings,
                "by_status": list(bookings_status)
            },
            "pending_approvals": {
                "registrations": pending_registrations,
                "bookings": pending_bookings,
                "resource_requests": pending_resource_requests,
                "role_changes": pending_role_changes
            },
            "most_booked_resources": list(most_booked)
        }
        
        return success_response(data)
