# ELD Backend - Electronic Logging Device App

This is the Django backend for a Full Stack ELD (Electronic Logging Device) application that helps truck drivers plan routes and automatically generates compliant Hours of Service logs based on FMCSA regulations.

## Features

- **Route Planning**: Calculate optimal routes with HOS compliance
- **Automatic HOS Log Generation**: Generate compliant daily logs based on FMCSA regulations
- **Trip Management**: Create and track trips with pickup/dropoff locations
- **RESTful API**: Django REST Framework API for frontend integration
- **PostgreSQL Support**: Production-ready database configuration

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Virtual environment (recommended)

### 2. Installation

1. Clone and navigate to the project:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and settings
```

5. Set up PostgreSQL database:
```sql
CREATE DATABASE eld_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE eld_db TO your_username;
```

6. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

7. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

8. Run the development server:
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Endpoints

### Trips
- `GET /api/trips/` - List all trips
- `POST /api/trips/create/` - Create a new trip with HOS planning
- `GET /api/trips/{trip_id}/` - Get specific trip details

### Trip Creation Example
```json
POST /api/trips/create/
{
    "current_location": "Chicago, IL",
    "current_lat": "41.8781",
    "current_lng": "-87.6298",
    "pickup_location": "Milwaukee, WI",
    "pickup_lat": "43.0389",
    "pickup_lng": "-87.9065",
    "dropoff_location": "Minneapolis, MN",
    "dropoff_lat": "44.9778",
    "dropoff_lng": "-93.2650",
    "current_cycle_hours": "45.5",
    "driver_name": "John Smith",
    "carrier_name": "ABC Trucking",
    "truck_number": "TRK-001"
}
```

## HOS Compliance Features

The system automatically:
- Calculates driving times and required rest periods
- Enforces 11-hour driving limit
- Manages 14-hour duty period
- Schedules mandatory 30-minute breaks after 8 hours of driving
- Plans 10-hour rest periods when needed
- Tracks 70-hour/8-day cycle limits

## Database Models

- **Trip**: Main trip entity with origin, pickup, and dropoff locations
- **RouteSegment**: Individual segments of the trip (driving, rest, fuel stops)
- **DailyLog**: Daily HOS summaries
- **LogEntry**: Individual log entries within each daily log

## Development

### Running Tests
```bash
python manage.py test
```

### Making Migrations
```bash
python manage.py makemigrations eld_app
python manage.py migrate
```

### Admin Interface
Access the Django admin at `http://localhost:8000/admin/` to manage data directly.

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Configure proper `SECRET_KEY`
3. Set up production PostgreSQL database
4. Use gunicorn for serving:
```bash
gunicorn eld_project.wsgi:application
```

## Configuration

Key environment variables:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: Database settings
- `OPENROUTE_API_KEY`: Optional API key for better routing data