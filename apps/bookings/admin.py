from django.contrib import admin
from .models import Booking

class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'resource', 'booking_date', 'start_time', 'status')
    list_filter = ('status', 'booking_date')
    search_fields = ('user__email', 'resource__name')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Booking, BookingAdmin)
