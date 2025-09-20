# requirements.txt
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
psycopg2-binary==2.9.7
requests==2.31.0
python-decouple==3.8
gunicorn==21.2.0

# settings.py
import os
from decouple import config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'eld_app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eld_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'eld_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='eld_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# eld_app/models.py
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

# eld_app/serializers.py
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

# eld_app/services.py
import requests
from datetime import datetime, timedelta, time
from decimal import Decimal
from .models import Trip, RouteSegment, DailyLog, LogEntry
import math

class RouteService:
    @staticmethod
    def calculate_distance(lat1, lng1, lat2, lng2):
        """Calculate distance between two points using Haversine formula"""
        R = 3958.756  # Earth's radius in miles
        
        lat1_rad = math.radians(float(lat1))
        lng1_rad = math.radians(float(lng1))
        lat2_rad = math.radians(float(lat2))
        lng2_rad = math.radians(float(lng2))
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

    @staticmethod
    def get_route_data(start_lat, start_lng, end_lat, end_lng):
        """Get route data from OpenRouteService or fallback to distance calculation"""
        try:
            # Try OpenRouteService API (free tier)
            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            headers = {
                'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
                'Authorization': '5b3ce3597851110001cf6248YOUR_API_KEY',  # Replace with actual key
                'Content-Type': 'application/json; charset=utf-8'
            }
            body = {
                "coordinates": [[float(start_lng), float(start_lat)], [float(end_lng), float(end_lat)]],
                "format": "json"
            }
            
            response = requests.post(url, json=body, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                route = data['routes'][0]
                distance_km = route['summary']['distance'] / 1000
                duration_sec = route['summary']['duration']
                
                return {
                    'distance_miles': distance_km * 0.621371,
                    'duration_hours': duration_sec / 3600,
                    'geometry': route['geometry']
                }
        except:
            pass
        
        # Fallback to simple calculation
        distance = RouteService.calculate_distance(start_lat, start_lng, end_lat, end_lng)
        # Estimate driving time at 55 mph average
        duration = distance / 55
        
        return {
            'distance_miles': distance,
            'duration_hours': duration,
            'geometry': None
        }

class HOSService:
    """Hours of Service compliance service"""
    
    @staticmethod
    def plan_trip_segments(trip):
        """Plan trip segments considering HOS regulations"""
        segments = []
        current_cycle = float(trip.current_cycle_hours)
        
        # Calculate total trip distance
        to_pickup = RouteService.get_route_data(
            trip.current_lat, trip.current_lng,
            trip.pickup_lat, trip.pickup_lng
        )
        to_dropoff = RouteService.get_route_data(
            trip.pickup_lat, trip.pickup_lng,
            trip.dropoff_lat, trip.dropoff_lng
        )
        
        total_distance = to_pickup['distance_miles'] + to_dropoff['distance_miles']
        total_driving_time = to_pickup['duration_hours'] + to_dropoff['duration_hours']
        
        # Current to pickup
        segments.extend(HOSService._plan_segment(
            trip.current_location, trip.pickup_location,
            to_pickup['distance_miles'], to_pickup['duration_hours'],
            current_cycle, 1
        ))
        
        # Pickup activity (1 hour)
        segments.append({
            'start_location': trip.pickup_location,
            'end_location': trip.pickup_location,
            'distance_miles': 0,
            'duration_hours': 1,
            'segment_type': 'pickup',
            'order': len(segments) + 1
        })
        
        # Update cycle hours after pickup
        current_cycle += 1
        
        # Pickup to dropoff
        segments.extend(HOSService._plan_segment(
            trip.pickup_location, trip.dropoff_location,
            to_dropoff['distance_miles'], to_dropoff['duration_hours'],
            current_cycle, len(segments) + 1
        ))
        
        # Dropoff activity (1 hour)
        segments.append({
            'start_location': trip.dropoff_location,
            'end_location': trip.dropoff_location,
            'distance_miles': 0,
            'duration_hours': 1,
            'segment_type': 'dropoff',
            'order': len(segments) + 1
        })
        
        return segments

    @staticmethod
    def _plan_segment(start_loc, end_loc, distance, duration, current_cycle, start_order):
        """Plan a single driving segment with HOS compliance"""
        segments = []
        remaining_distance = distance
        remaining_duration = duration
        current_driving_time = 0
        current_duty_time = 0
        order = start_order
        
        while remaining_distance > 0:
            # Check if we need a 30-minute break (after 8 hours of driving)
            if current_driving_time >= 8:
                segments.append({
                    'start_location': f"Rest stop near {start_loc}",
                    'end_location': f"Rest stop near {start_loc}",
                    'distance_miles': 0,
                    'duration_hours': 0.5,
                    'segment_type': 'break',
                    'order': order
                })
                order += 1
                current_driving_time = 0
                current_duty_time += 0.5
            
            # Check if we need a 10-hour rest period
            if current_duty_time >= 14 or current_cycle >= 70:
                segments.append({
                    'start_location': f"Rest area near {start_loc}",
                    'end_location': f"Rest area near {start_loc}",
                    'distance_miles': 0,
                    'duration_hours': 10,
                    'segment_type': 'rest',
                    'order': order
                })
                order += 1
                current_driving_time = 0
                current_duty_time = 0
                current_cycle = 0  # Reset after 34-hour restart (simplified)
            
            # Calculate how much we can drive before next break/rest
            max_driving = min(11 - current_driving_time, 8)  # 11-hour limit, 8 before break
            max_duty = 14 - current_duty_time
            
            driving_time = min(remaining_duration, max_driving, max_duty)
            segment_distance = (driving_time / duration) * distance if duration > 0 else 0
            
            # Add fuel stop if needed (every 1000 miles)
            total_driven = distance - remaining_distance
            if total_driven > 0 and int(total_driven) % 1000 < int(total_driven + segment_distance) % 1000:
                segments.append({
                    'start_location': f"Fuel stop near {start_loc}",
                    'end_location': f"Fuel stop near {start_loc}",
                    'distance_miles': 0,
                    'duration_hours': 0.5,
                    'segment_type': 'fuel',
                    'order': order
                })
                order += 1
                current_duty_time += 0.5
            
            # Add driving segment
            segments.append({
                'start_location': start_loc,
                'end_location': end_loc if remaining_distance <= segment_distance else f"En route to {end_loc}",
                'distance_miles': segment_distance,
                'duration_hours': driving_time,
                'segment_type': 'driving',
                'order': order
            })
            
            remaining_distance -= segment_distance
            remaining_duration -= driving_time
            current_driving_time += driving_time
            current_duty_time += driving_time
            current_cycle += driving_time
            order += 1
            
            if remaining_distance <= 0:
                break
        
        return segments

    @staticmethod
    def generate_daily_logs(trip, segments):
        """Generate daily log entries from trip segments"""
        daily_logs = {}
        current_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)  # Start at 6 AM
        
        for segment in segments:
            date = current_time.date()
            
            if date not in daily_logs:
                daily_logs[date] = {
                    'date': date,
                    'entries': [],
                    'total_miles': 0,
                    'total_hours_off_duty': 0,
                    'total_hours_sleeper': 0,
                    'total_hours_driving': 0,
                    'total_hours_on_duty': 0
                }
            
            start_time = current_time.time()
            end_time = (current_time + timedelta(hours=float(segment['duration_hours']))).time()
            
            # Map segment types to duty status
            duty_status_map = {
                'driving': 'driving',
                'pickup': 'on_duty_not_driving',
                'dropoff': 'on_duty_not_driving',
                'fuel': 'on_duty_not_driving',
                'break': 'off_duty',
                'rest': 'sleeper_berth'
            }
            
            duty_status = duty_status_map.get(segment['segment_type'], 'on_duty_not_driving')
            
            # Create log entry
            entry = {
                'start_time': start_time,
                'end_time': end_time,
                'duty_status': duty_status,
                'location': segment['start_location'],
                'remarks': f"{segment['segment_type'].title()} - {segment['start_location']} to {segment['end_location']}"
            }
            
            daily_logs[date]['entries'].append(entry)
            
            # Update totals
            hours = float(segment['duration_hours'])
            daily_logs[date]['total_miles'] += float(segment['distance_miles'])
            
            if duty_status == 'off_duty':
                daily_logs[date]['total_hours_off_duty'] += hours
            elif duty_status == 'sleeper_berth':
                daily_logs[date]['total_hours_sleeper'] += hours
            elif duty_status == 'driving':
                daily_logs[date]['total_hours_driving'] += hours
            else:
                daily_logs[date]['total_hours_on_duty'] += hours
            
            # Advance time
            current_time += timedelta(hours=hours)
            
            # If we cross midnight, ensure proper day transition
            if current_time.date() > date and current_time.time() < time(6, 0):
                current_time = current_time.replace(hour=6, minute=0)
        
        return list(daily_logs.values())

# eld_app/views.py
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Trip, RouteSegment, DailyLog, LogEntry
from .serializers import TripSerializer, TripCreateSerializer
from .services import HOSService
from decimal import Decimal

@api_view(['POST'])
def create_trip(request):
    """Create a new trip and generate route plan with HOS compliance"""
    serializer = TripCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    trip = serializer.save()
    
    try:
        # Generate route segments
        segments = HOSService.plan_trip_segments(trip)
        
        # Save route segments
        for segment_data in segments:
            RouteSegment.objects.create(trip=trip, **segment_data)
        
        # Generate daily logs
        daily_logs_data = HOSService.generate_daily_logs(trip, segments)
        
        # Save daily logs and entries
        for log_data in daily_logs_data:
            entries_data = log_data.pop('entries')
            daily_log = DailyLog.objects.create(
                trip=trip,
                date=log_data['date'],
                total_miles=Decimal(str(log_data['total_miles'])),
                total_hours_off_duty=Decimal(str(log_data['total_hours_off_duty'])),
                total_hours_sleeper=Decimal(str(log_data['total_hours_sleeper'])),
                total_hours_driving=Decimal(str(log_data['total_hours_driving'])),
                total_hours_on_duty=Decimal(str(log_data['total_hours_on_duty']))
            )
            
            for entry_data in entries_data:
                LogEntry.objects.create(daily_log=daily_log, **entry_data)
        
        # Return complete trip data
        trip_serializer = TripSerializer(trip)
        return Response(trip_serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        trip.delete()  # Clean up if something goes wrong
        return Response(
            {'error': f'Failed to generate trip plan: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_trip(request, trip_id):
    """Get trip details by ID"""
    try:
        trip = Trip.objects.get(id=trip_id)
        serializer = TripSerializer(trip)
        return Response(serializer.data)
    except Trip.DoesNotExist:
        return Response(
            {'error': 'Trip not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
def list_trips(request):
    """List all trips"""
    trips = Trip.objects.all().order_by('-created_at')
    serializer = TripSerializer(trips, many=True)
    return Response(serializer.data)

# eld_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('trips/', views.list_trips, name='list_trips'),
    path('trips/create/', views.create_trip, name='create_trip'),
    path('trips/<uuid:trip_id>/', views.get_trip, name='get_trip'),
]

# eld_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('eld_app.urls')),
]