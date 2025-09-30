from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # API endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/properties/', include('apps.properties.urls')),
    path('api/vehicles/', include('apps.vehicles.urls')),
    path('api/common-areas/', include('apps.common_areas.urls')),
    path('api/communications/', include('apps.communications.urls')),
    path('api/reservations/', include('apps.reservations.urls')),
    path('api/access-control/', include('apps.access_control.urls')),
    path('api/visitor-control/', include('apps.visitor_control.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)