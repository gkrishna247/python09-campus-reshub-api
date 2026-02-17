from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for User management.

    Supports filtering by status via ?status=ACTIVE or ?status=INACTIVE.
    """

    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer

    def get_queryset(self):
        """Filter users by status query parameter if provided."""
        queryset = super().get_queryset()
        user_status = self.request.query_params.get("status")
        if user_status:
            queryset = queryset.filter(status=user_status.upper())
        return queryset

    def list(self, request, *args, **kwargs):
        """Return paginated list with success wrapper."""
        response = super().list(request, *args, **kwargs)
        return Response(
            {
                "success": True,
                "count": response.data.get("count", 0),
                "next": response.data.get("next"),
                "previous": response.data.get("previous"),
                "data": response.data.get("results", []),
            }
        )

    def retrieve(self, request, *args, **kwargs):
        """Return single user with success wrapper."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})

    def create(self, request, *args, **kwargs):
        """Create user and return with success wrapper."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """Update user (supports partial) and return with success wrapper."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH as partial update."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete user and return 204."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
