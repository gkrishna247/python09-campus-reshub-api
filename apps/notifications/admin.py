from django.contrib import admin
from .models import UserNotification

class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_type', 'title', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read')
    search_fields = ('user__email', 'title', 'body')
    readonly_fields = ('created_at',)

admin.site.register(UserNotification, UserNotificationAdmin)
