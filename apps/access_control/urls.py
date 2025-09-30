# apps/access_control/urls.py

from django.urls import path
from . import views

app_name = 'access_control'

urlpatterns = [
    # Crear y Listar registros de acceso
    path('logs/', views.AccessLogListCreateView.as_view(), name='access_log_list_create'),
    
    # Obtener los logs más recientes (útil para dashboards)
    path('logs/latest/', views.latest_access_attempts, name='latest_access_attempts'),
    path('logs/latest/<int:limit>/', views.latest_access_attempts, name='latest_access_attempts_limit'),
]