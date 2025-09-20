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
        # Estimate driving time at realistic speeds:
        # - Urban/short distance: 45 mph average
        # - Long distance highway: 60 mph average
        if distance < 50:
            avg_speed = 45  # Urban driving
        else:
            avg_speed = 60  # Highway driving
        
        duration = distance / avg_speed

        return {
            'distance_miles': round(distance, 2),
            'duration_hours': round(duration, 2),
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

        # If the trip is short (under 8 hours), don't add mandatory rest periods
        if duration <= 8 and distance <= 550:  # Under 8 hours and 550 miles
            # Just add the driving segment without mandatory breaks
            segments.append({
                'start_location': start_loc,
                'end_location': end_loc,
                'distance_miles': distance,
                'duration_hours': duration,
                'segment_type': 'driving',
                'order': order
            })
            return segments

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

            # Check if we need a 10-hour rest period (only for long trips)
            if current_duty_time >= 14:
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

            # Calculate how much we can drive before next break/rest
            max_driving_before_break = 8 - current_driving_time
            max_driving_daily = 11 - current_driving_time
            max_duty = 14 - current_duty_time

            # Use the most restrictive limit
            max_driving = min(max_driving_before_break, max_driving_daily, max_duty, remaining_duration)

            if max_driving <= 0:
                continue

            # Calculate distance for this driving segment
            segment_distance = min(remaining_distance, (max_driving / duration) * distance if duration > 0 else remaining_distance)

            # Add driving segment
            segments.append({
                'start_location': start_loc,
                'end_location': end_loc if segment_distance >= remaining_distance else f"En route to {end_loc}",
                'distance_miles': round(segment_distance, 2),
                'duration_hours': round(max_driving, 2),
                'segment_type': 'driving',
                'order': order
            })

            remaining_distance -= segment_distance
            remaining_duration -= max_driving
            current_driving_time += max_driving
            current_duty_time += max_driving
            order += 1

            if remaining_distance <= 0.1:  # Small threshold to avoid rounding errors
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