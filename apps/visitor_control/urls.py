# apps/visitor_control/urls.py
from django.urls import path
from . import views

app_name = 'visitor_control'

urlpatterns = [
    # CRUD y Listado Principal (Visitantes Activos)
    path('', views.VisitorLogListCreateView.as_view(), name='visitor_log_list_create'),
    path('<int:pk>/', views.VisitorLogDetailUpdateView.as_view(), name='visitor_log_detail_update'),
    
    # Funcionalidades Específicas
    path('<int:log_id>/check-out/', views.check_out_visitor_view, name='check_out_visitor'),
    
    # Datos para el Formulario
    path('form-data/', views.get_visitor_form_data, name='visitor_form_data'),
]