from rest_framework import serializers
from .models import Trip, RouteSegment, DailyLog, LogEntry

class RouteSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteSegment
        fields = '__all__'

class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = '__all__'

class DailyLogSerializer(serializers.ModelSerializer):
    log_entries = LogEntrySerializer(many=True, read_only=True)

    class Meta:
        model = DailyLog
        fields = '__all__'

class TripSerializer(serializers.ModelSerializer):
    route_segments = RouteSegmentSerializer(many=True, read_only=True)
    daily_logs = DailyLogSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = '__all__'

class TripCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = [
            'current_location', 'current_lat', 'current_lng',
            'pickup_location', 'pickup_lat', 'pickup_lng',
            'dropoff_location', 'dropoff_lat', 'dropoff_lng',
            'current_cycle_hours', 'driver_name', 'carrier_name', 'truck_number'
        ]