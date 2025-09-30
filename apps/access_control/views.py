# apps/access_control/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import AccessLog
from .serializers import AccessLogCreateSerializer, AccessLogSerializer
from django.db.models import F # Para usar F() expressions si fuera necesario

class AccessLogListCreateView(generics.ListCreateAPIView):
    """
    POST: Registra un nuevo intento de acceso.
    GET: Lista los últimos intentos de acceso registrados.
    """
    queryset = AccessLog.objects.all()
    # Permitir a usuarios de seguridad/cámara crear, y a admins/seguridad listar.
    # Por ahora, solo restringiremos a autenticados, puedes ajustar.
    permission_classes = [permissions.IsAuthenticated] 
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AccessLogCreateSerializer
        return AccessLogSerializer
    
    def get_queryset(self):
        # Mostrar los últimos 50 registros por defecto
        return AccessLog.objects.all().select_related('resident').order_by('-access_time')[:50]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def latest_access_attempts(request, limit=5):
    """Obtener los N intentos de acceso más recientes"""
    latest_logs = AccessLog.objects.all().select_related('resident').order_by('-access_time')[:limit]
    serializer = AccessLogSerializer(latest_logs, many=True)
    
    return Response({
        'message': f'Últimos {limit} intentos de acceso registrados',
        'logs': serializer.data
    }, status=status.HTTP_200_OK)