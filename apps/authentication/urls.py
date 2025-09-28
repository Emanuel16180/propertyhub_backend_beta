from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Autenticación
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.refresh_token_view, name='refresh_token'),
    path('verify/', views.verify_token_view, name='verify_token'),
    path('profile/', views.profile_view, name='profile'),
]