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
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)