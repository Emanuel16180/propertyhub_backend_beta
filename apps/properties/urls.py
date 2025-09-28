from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    # CRUD básico de propiedades
    path('', views.PropertyListCreateView.as_view(), name='property_list_create'),
    path('<int:pk>/', views.PropertyDetailView.as_view(), name='property_detail'),
    
    # Gestión de propietarios
    path('<int:property_id>/assign-owner/', views.assign_owner_view, name='assign_owner'),
    path('<int:property_id>/remove-owner/', views.remove_owner_view, name='remove_owner'),
    
    # Gestión de residentes
    path('<int:property_id>/add-resident/', views.add_resident_to_property_view, name='add_resident'),
    path('with-residents/', views.properties_with_residents_view, name='properties_with_residents'),
    
    # Filtros y consultas
    path('status/<str:status_type>/', views.properties_by_status_view, name='properties_by_status'),
    path('stats/', views.property_stats_view, name='property_stats'),
]