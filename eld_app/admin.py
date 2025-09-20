from django.contrib import admin
from .models import Trip, RouteSegment, DailyLog, LogEntry

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'driver_name', 'carrier_name', 'truck_number', 'created_at']
    list_filter = ['created_at', 'carrier_name']
    search_fields = ['driver_name', 'carrier_name', 'truck_number']
    readonly_fields = ['id', 'created_at']

@admin.register(RouteSegment)
class RouteSegmentAdmin(admin.ModelAdmin):
    list_display = ['trip', 'segment_type', 'start_location', 'end_location', 'distance_miles', 'duration_hours']
    list_filter = ['segment_type']
    search_fields = ['start_location', 'end_location']

@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ['trip', 'date', 'total_miles', 'total_hours_driving']
    list_filter = ['date']
    date_hierarchy = 'date'

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['daily_log', 'start_time', 'end_time', 'duty_status', 'location']
    list_filter = ['duty_status', 'daily_log__date']
    search_fields = ['location', 'remarks']