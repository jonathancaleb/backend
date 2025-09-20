from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from datetime import datetime, timedelta

class Trip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    current_location = models.CharField(max_length=255)
    current_lat = models.DecimalField(max_digits=9, decimal_places=6)
    current_lng = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_location = models.CharField(max_length=255)
    pickup_lat = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_lng = models.DecimalField(max_digits=9, decimal_places=6)
    dropoff_location = models.CharField(max_length=255)
    dropoff_lat = models.DecimalField(max_digits=9, decimal_places=6)
    dropoff_lng = models.DecimalField(max_digits=9, decimal_places=6)
    current_cycle_hours = models.DecimalField(
        max_digits=4, decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(70)]
    )
    driver_name = models.CharField(max_length=100)
    carrier_name = models.CharField(max_length=200)
    truck_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip {self.id} - {self.driver_name}"

class RouteSegment(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='route_segments')
    start_location = models.CharField(max_length=255)
    end_location = models.CharField(max_length=255)
    distance_miles = models.DecimalField(max_digits=8, decimal_places=2)
    duration_hours = models.DecimalField(max_digits=4, decimal_places=2)
    segment_type = models.CharField(max_length=50, choices=[
        ('driving', 'Driving'),
        ('rest', 'Rest'),
        ('fuel', 'Fuel Stop'),
        ('pickup', 'Pickup'),
        ('dropoff', 'Drop-off'),
        ('break', '30-min Break')
    ])
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

class DailyLog(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='daily_logs')
    date = models.DateField()
    total_miles = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_hours_off_duty = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    total_hours_sleeper = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    total_hours_driving = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    total_hours_on_duty = models.DecimalField(max_digits=4, decimal_places=2, default=0)

    class Meta:
        ordering = ['date']

class LogEntry(models.Model):
    DUTY_STATUS_CHOICES = [
        ('off_duty', 'Off Duty'),
        ('sleeper_berth', 'Sleeper Berth'),
        ('driving', 'Driving'),
        ('on_duty_not_driving', 'On Duty (Not Driving)')
    ]

    daily_log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='log_entries')
    start_time = models.TimeField()
    end_time = models.TimeField()
    duty_status = models.CharField(max_length=20, choices=DUTY_STATUS_CHOICES)
    location = models.CharField(max_length=255)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['start_time']