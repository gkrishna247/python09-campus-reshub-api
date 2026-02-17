from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import Booking
from .serializers import BookingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Booking management.

    Includes double-booking conflict detection (409 Conflict).
    Responses include nested user and resource details.
    """

    queryset = Booking.objects.select_related("user", "resource").all().order_by("id")
    serializer_class = BookingSerializer

    def _check_conflict(self, data, instance=None):
        """
        Check for double-booking conflicts.
        Returns a 409 Response if conflict found, else None.
        """
        resource_id = data.get("resource_id")
        booking_date = data.get("booking_date")
        time_slot = data.get("time_slot")

        # For updates, use existing values if not provided
        if instance:
            resource_id = resource_id or instance.resource_id
            booking_date = booking_date or instance.booking_date
            time_slot = time_slot or instance.time_slot

        if resource_id and booking_date and time_slot:
            conflicting = Booking.objects.filter(
                resource_id=resource_id,
                booking_date=booking_date,
                time_slot=time_slot,
                status__in=["PENDING", "APPROVED"],
            )
            if instance:
                conflicting = conflicting.exclude(pk=instance.pk)

            if conflicting.exists():
                return Response(
                    {
                        "success": False,
                        "message": "This resource is already booked for the selected date and time slot.",
                        "errors": {},
                    },
                    status=status.HTTP_409_CONFLICT,
                )
        return None

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
        """Return single booking with success wrapper."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})

    def create(self, request, *args, **kwargs):
        """Create booking with conflict detection and success wrapper."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check for double booking — return 409 if conflict
        conflict_response = self._check_conflict(serializer.validated_data)
        if conflict_response:
            return conflict_response

        instance = serializer.save()

        # Re-serialize with nested objects for the response
        output_serializer = BookingSerializer(instance)
        return Response(
            {"success": True, "data": output_serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """Update booking (supports partial) with conflict re-validation."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Check for double booking — return 409 if conflict
        conflict_response = self._check_conflict(serializer.validated_data, instance)
        if conflict_response:
            return conflict_response

        updated_instance = serializer.save()

        # Re-serialize with nested objects for the response
        output_serializer = BookingSerializer(updated_instance)
        return Response({"success": True, "data": output_serializer.data})

    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH as partial update."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete booking and return 204."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
