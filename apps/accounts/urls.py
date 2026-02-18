from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, ApprovalStatusView,
    UserListView, UserDetailView, ProfileView, ChangePasswordView,
    PendingRegistrationsView, ApproveRegistrationView, RejectRegistrationView,
    RoleChangeRequestCreateView, RoleChangeRequestListView, MyRoleChangeRequestsView,
    ApproveRoleChangeView, RejectRoleChangeView, StatisticsView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/approval-status/", ApprovalStatusView.as_view(), name="approval-status"),
    
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/change-password/", ChangePasswordView.as_view(), name="change-password"),
    
    path("approvals/registrations/", PendingRegistrationsView.as_view(), name="pending-registrations"),
    path("approvals/registrations/<int:pk>/approve/", ApproveRegistrationView.as_view(), name="approve-registration"),
    path("approvals/registrations/<int:pk>/reject/", RejectRegistrationView.as_view(), name="reject-registration"),
    
    path("role-changes/", RoleChangeRequestCreateView.as_view(), name="role-change-create"),
    path("role-changes/list/", RoleChangeRequestListView.as_view(), name="role-change-list"),
    path("role-changes/my/", MyRoleChangeRequestsView.as_view(), name="my-role-changes"),
    path("role-changes/<int:pk>/approve/", ApproveRoleChangeView.as_view(), name="approve-role-change"),
    path("role-changes/<int:pk>/reject/", RejectRoleChangeView.as_view(), name="reject-role-change"),
    
    path("statistics/", StatisticsView.as_view(), name="statistics"),
]
