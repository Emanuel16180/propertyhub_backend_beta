# apps/security/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import IntrusionLog
from .serializers import (
    IntrusionLogSerializer,
    IntrusionLogCreateSerializer,
    IntrusionLogUpdateSerializer
)

class IntrusionLogListCreateView(generics.ListCreateAPIView):
    """
    GET: Lista todos los registros de intrusión (por defecto, no resueltos).
    POST: Crea un nuevo registro de intrusión (alerta).
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = IntrusionLog.objects.all().select_related('resolved_by')
        
        # Filtro para ver solo no resueltos
        if self.request.query_params.get('resolved') == 'false' or not self.request.query_params.get('resolved'):
            queryset = queryset.filter(is_resolved=False)
            
        # Filtro por cámara
        camera = self.request.query_params.get('camera', None)
        if camera:
            queryset = queryset.filter(camera_identifier__icontains=camera)
            
        return queryset.order_by('-detection_time')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IntrusionLogCreateSerializer
        return IntrusionLogSerializer

class IntrusionLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Detalle de un registro.
    PUT/PATCH: Actualiza el registro.
    DELETE: Elimina el registro.
    """
    queryset = IntrusionLog.objects.all().select_related('resolved_by')
    serializer_class = IntrusionLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            # Podrías usar IntrusionLogUpdateSerializer aquí para restringir campos si lo deseas
            return IntrusionLogSerializer 
        return IntrusionLogSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_resolved_view(request, log_id):
    """Endpoint para que un usuario marque una intrusión como resuelta."""
    intrusion_log = get_object_or_404(IntrusionLog, id=log_id)
    
    if intrusion_log.is_resolved:
        return Response({
            'message': 'Esta alerta ya estaba marcada como resuelta.'
        }, status=status.HTTP_200_OK)
    
    # Marcar como resuelto y asignar al usuario actual
    intrusion_log.is_resolved = True
    intrusion_log.resolved_by = request.user
    intrusion_log.save()
    
    response_serializer = IntrusionLogSerializer(intrusion_log)
    
    return Response({
        'message': f'Alerta {log_id} marcada como resuelta por {request.user.get_full_name()}',
        'log': response_serializer.data
    }, status=status.HTTP_200_OK)