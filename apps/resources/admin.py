from django.contrib import admin
from .models import Resource, ResourceAdditionRequest, ResourceWeeklySchedule, CalendarOverride

class ResourceWeeklyScheduleInline(admin.TabularInline):
    model = ResourceWeeklySchedule
    extra = 0
    can_delete = False
    fields = ('day_of_week', 'start_time', 'end_time', 'is_working')

class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'capacity', 'resource_status', 'approval_type', 'managed_by')
    list_filter = ('type', 'resource_status', 'approval_type')
    search_fields = ('name', 'location')
    inlines = [ResourceWeeklyScheduleInline]

class ResourceAdditionRequestAdmin(admin.ModelAdmin):
    list_display = ('proposed_name', 'requested_by', 'status', 'created_at')
    list_filter = ('status', 'proposed_type')
    search_fields = ('proposed_name', 'requested_by__email')

class CalendarOverrideAdmin(admin.ModelAdmin):
    list_display = ('override_date', 'override_type', 'description', 'created_by')
    list_filter = ('override_type',)
    ordering = ('override_date',)

admin.site.register(Resource, ResourceAdmin)
admin.site.register(ResourceAdditionRequest, ResourceAdditionRequestAdmin)
admin.site.register(ResourceWeeklySchedule) # Optional if inline is enough, but good for direct access
admin.site.register(CalendarOverride, CalendarOverrideAdmin)
