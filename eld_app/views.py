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