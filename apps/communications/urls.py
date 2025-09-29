# apps/communications/urls.py
from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    # CRUD básico de comunicados
    path('', views.CommunicationListCreateView.as_view(), name='communication-list-create'),
    path('<int:pk>/', views.CommunicationDetailView.as_view(), name='communication-detail'),
    
    # Funcionalidades adicionales
    path('<int:communication_id>/mark-read/', views.mark_as_read, name='mark-as-read'),
    path('my-communications/', views.my_communications, name='my-communications'),
    path('urgent/', views.urgent_communications, name='urgent-communications'),
    path('stats/', views.communication_stats, name='communication-stats'),
]