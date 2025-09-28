from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    # CRUD básico de vehículos
    path('', views.VehicleListCreateView.as_view(), name='vehicle_list_create'),
    path('<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle_detail'),
    
    # Endpoint para obtener residentes (para el dropdown del formulario)
    path('residents/', views.residents_for_vehicles_view, name='residents_for_vehicles'),
    
    # Filtros y consultas
    path('type/<str:vehicle_type>/', views.vehicles_by_type_view, name='vehicles_by_type'),
    path('resident/<int:resident_id>/', views.vehicles_by_resident_view, name='vehicles_by_resident'),
    path('search/', views.search_vehicles_view, name='search_vehicles'),
    
    # Gestión de propietarios
    path('<int:vehicle_id>/change-owner/', views.change_vehicle_owner_view, name='change_vehicle_owner'),
    
    # Estadísticas
    path('stats/', views.vehicle_stats_view, name='vehicle_stats'),
]