# apps/security/urls.py

from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    # CRUD y Listado de logs de intrusión
    path('intrusions/', views.IntrusionLogListCreateView.as_view(), name='intrusion_log_list_create'),
    path('intrusions/<int:pk>/', views.IntrusionLogDetailView.as_view(), name='intrusion_log_detail'),
    
    # Funcionalidad específica: Resolver alerta
    path('intrusions/<int:log_id>/resolve/', views.mark_as_resolved_view, name='mark_as_resolved'),
]