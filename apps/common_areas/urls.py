from django.urls import path
from . import views

app_name = 'common_areas'

urlpatterns = [
    # CRUD básico de áreas comunes
    path('', views.CommonAreaListCreateView.as_view(), name='area_list_create'),
    path('<int:pk>/', views.CommonAreaDetailView.as_view(), name='area_detail'),
    
    # Filtros y consultas
    path('type/<str:area_type>/', views.areas_by_type_view, name='areas_by_type'),
    path('available/', views.available_areas_view, name='available_areas'),
    path('reservation-required/', views.areas_requiring_reservation_view, name='areas_requiring_reservation'),
    path('search/', views.search_areas_view, name='search_areas'),
    
    # Gestión de disponibilidad
    path('<int:area_id>/check-availability/', views.check_area_availability_view, name='check_area_availability'),
    path('<int:area_id>/toggle-maintenance/', views.toggle_maintenance_view, name='toggle_maintenance'),
    
    # Información general
    path('types/', views.area_types_view, name='area_types'),
    path('stats/', views.common_area_stats_view, name='area_stats'),
]