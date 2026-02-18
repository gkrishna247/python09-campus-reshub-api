from django.contrib import admin
from .models import AuditLog

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'actor_email', 'target_entity_type', 'target_entity_id')
    list_filter = ('action', 'target_entity_type')
    search_fields = ('action', 'actor_email', 'target_entity_type')
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(AuditLog, AuditLogAdmin)
