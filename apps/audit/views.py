from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .serializers import AuditLogSerializer
from .models import AuditLog
from core.permissions import IsActiveAndApproved, IsAdmin
from core.response import success_response

class AuditLogListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsActiveAndApproved, IsAdmin]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
            
        actor_id = self.request.query_params.get('actor_id')
        if actor_id:
            queryset = queryset.filter(actor__id=actor_id)
            
        target_entity_type = self.request.query_params.get('target_entity_type')
        if target_entity_type:
             queryset = queryset.filter(target_entity_type=target_entity_type)
             
        from_date = self.request.query_params.get('from_date')
        if from_date:
             queryset = queryset.filter(timestamp__date__gte=from_date)
             
        to_date = self.request.query_params.get('to_date')
        if to_date:
             queryset = queryset.filter(timestamp__date__lte=to_date)
             
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(action__icontains=search) | Q(actor_email__icontains=search))
            
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)
