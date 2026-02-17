from rest_framework import generics, views, status
from rest_framework.permissions import IsAuthenticated
from .serializers import NotificationSerializer
from .models import UserNotification
from core.permissions import IsActiveAndApproved
from core.response import success_response, error_response

class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user)[:20]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

class MarkNotificationReadView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]

    def patch(self, request, pk):
        try:
            notification = UserNotification.objects.get(pk=pk)
        except UserNotification.DoesNotExist:
            return error_response(message="Notification not found.", status_code=404)
            
        if notification.user != request.user:
            return error_response(message="Permission denied.", status_code=403)
            
        notification.is_read = True
        notification.save()
        return success_response(message="Notification marked as read.")

class MarkAllNotificationsReadView(views.APIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved]

    def post(self, request):
        UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return success_response(message="All notifications marked as read.")
