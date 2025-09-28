from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # CRUD básico de usuarios
    path('', views.UserListCreateView.as_view(), name='user_list_create'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    
    # Filtros y listados especiales
    path('type/<str:user_type>/', views.users_by_type_view, name='users_by_type'),
    path('residents/detail/', views.residents_detail_view, name='residents_detail'),
    
    # Gestión de casas para residentes
    path('<int:user_id>/assign-house/', views.assign_house_to_resident_view, name='assign_house_to_resident'),
    path('<int:user_id>/remove-house/', views.remove_house_from_resident_view, name='remove_house_from_resident'),
    path('residents/without-house/', views.residents_without_house_view, name='residents_without_house'),
    path('residents/with-house/', views.residents_with_house_view, name='residents_with_house'),
    
    # Actualización de perfiles
    path('<int:user_id>/profile/update/', views.update_user_profile_view, name='update_user_profile'),
    path('<int:user_id>/resident/profile/', views.create_resident_profile_view, name='create_resident_profile'),
    path('<int:user_id>/resident/photo/', views.upload_resident_photo_view, name='upload_resident_photo'),
    
    # Estadísticas
    path('stats/', views.user_stats_view, name='user_stats'),
]