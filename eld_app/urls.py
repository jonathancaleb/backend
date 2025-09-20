from django.urls import path
from . import views

urlpatterns = [
    path('trips/', views.list_trips, name='list_trips'),
    path('trips/create/', views.create_trip, name='create_trip'),
    path('trips/<uuid:trip_id>/', views.get_trip, name='get_trip'),
]