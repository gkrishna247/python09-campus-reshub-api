from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, RoleChangeRequest

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'role', 'account_status', 'approval_status', 'is_staff')
    list_filter = ('role', 'account_status', 'approval_status', 'is_staff')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone')}),
        ('Permissions', {'fields': ('role', 'account_status', 'approval_status', 'rejection_reason', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password', 'confirm_password'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('email', 'name')
    ordering = ('email',)

class RoleChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_role', 'requested_role', 'status', 'created_at')
    list_filter = ('status', 'requested_role')
    search_fields = ('user__email', 'user__name')
    readonly_fields = ('created_at', 'reviewed_at')

admin.site.register(User, UserAdmin)
admin.site.register(RoleChangeRequest, RoleChangeRequestAdmin)
