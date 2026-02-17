from rest_framework import permissions

class IsActiveAndApproved(permissions.BasePermission):
    """
    Allocates access only to active and approved users.
    """
    message = "Account is inactive or not approved."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.account_status != "ACTIVE":
            self.message = "Account is inactive."
            return False
        
        if request.user.approval_status != "APPROVED":
            self.message = "Account not yet approved."
            return False
            
        return True

class IsAdmin(permissions.BasePermission):
    """
    Allocates access only to ADMIN users.
    """
    message = "Admin access required."

    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == "ADMIN"
        )

class IsStaffRole(permissions.BasePermission):
    """
    Allocates access only to STAFF users.
    """
    message = "Staff access required."

    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == "STAFF"
        )

class IsFacultyOrAdmin(permissions.BasePermission):
    """
    Allocates access only to FACULTY or ADMIN users.
    """
    message = "Faculty or Admin access required."

    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == "FACULTY" or request.user.role == "ADMIN")
        )

class CanBook(permissions.BasePermission):
    """
    Allocates access to STUDENT, FACULTY, and ADMIN. STAFF cannot book.
    """
    message = "Staff members cannot create bookings."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ["STUDENT", "FACULTY", "ADMIN"]

class IsResourceManager(permissions.BasePermission):
    """
    Object-level permission to only allow managers of a resource to edit it.
    """
    message = "You are not the manager for this resource."

    def has_object_permission(self, request, view, obj):
        # Check if obj is Resource or Booking (has resource attribute)
        if hasattr(obj, 'managed_by'):
             return obj.managed_by == request.user
        elif hasattr(obj, 'resource') and hasattr(obj.resource, 'managed_by'):
             return obj.resource.managed_by == request.user
        return False
