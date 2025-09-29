# apps/reservations/urls.py
from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # CRUD básico de reservas
    path('', views.ReservationListCreateView.as_view(), name='reservation-list-create'),
    path('<int:pk>/', views.ReservationDetailView.as_view(), name='reservation-detail'),
    
    # Datos para el formulario de reserva
    path('common-areas/', views.available_common_areas_view, name='available-common-areas'),
    path('properties/', views.available_properties_view, name='available-properties'),
    path('residents-by-property/', views.residents_by_property_view, name='residents-by-property'),
    path('available-time-slots/', views.available_time_slots_view, name='available-time-slots'),
    
    # Gestión de reservas
    path('my-reservations/', views.my_reservations_view, name='my-reservations'),
    path('<int:reservation_id>/cancel/', views.cancel_reservation_view, name='cancel-reservation'),
    
    # Consultas y filtros
    path('by-area/<int:area_id>/', views.reservations_by_area_view, name='reservations-by-area'),
    path('by-date/', views.reservations_by_date_view, name='reservations-by-date'),
    path('upcoming/', views.upcoming_reservations_view, name='upcoming-reservations'),
    
    # Utilidades
    path('check-availability/', views.check_availability_view, name='check-availability'),
    path('stats/', views.reservation_stats_view, name='reservation-stats'),
]