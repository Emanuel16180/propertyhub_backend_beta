from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import CommonArea
from .serializers import (
    CommonAreaCreateSerializer,
    CommonAreaSerializer,
    CommonAreaUpdateSerializer,
    CommonAreaSimpleSerializer,
    CommonAreaAvailabilitySerializer
)

class CommonAreaListCreateView(generics.ListCreateAPIView):
    """Vista para listar todas las áreas comunes y crear nuevas"""
    queryset = CommonArea.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommonAreaCreateSerializer
        return CommonAreaSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear nueva área común"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        area = serializer.save()
        
        # Retornar el área creada con datos completos
        response_serializer = CommonAreaSerializer(area)
        
        return Response({
            'message': 'Área común registrada exitosamente',
            'area': response_serializer.data
        }, status=status.HTTP_201_CREATED)

class CommonAreaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar un área común específica"""
    queryset = CommonArea.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CommonAreaUpdateSerializer
        return CommonAreaSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar área común con mensaje personalizado"""
        instance = self.get_object()
        area_name = instance.name
        self.perform_destroy(instance)
        
        return Response({
            'message': f'Área común "{area_name}" eliminada exitosamente'
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def areas_by_type_view(request, area_type):
    """Obtener áreas comunes filtradas por tipo"""
    valid_types = [choice[0] for choice in CommonArea.AREA_TYPES]
    
    if area_type not in valid_types:
        return Response({
            'error': f'Tipo de área inválido. Tipos válidos: {", ".join(valid_types)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    areas = CommonArea.objects.filter(area_type=area_type)
    serializer = CommonAreaSerializer(areas, many=True)
    
    type_display = dict(CommonArea.AREA_TYPES)[area_type]
    
    return Response({
        'area_type': area_type,
        'type_display': type_display,
        'count': areas.count(),
        'areas': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_areas_view(request):
    """Obtener solo las áreas comunes disponibles (activas y no en mantenimiento)"""
    available_areas = CommonArea.objects.filter(
        is_active=True, 
        is_maintenance=False
    )
    
    serializer = CommonAreaSerializer(available_areas, many=True)
    
    return Response({
        'message': 'Áreas comunes disponibles',
        'count': available_areas.count(),
        'areas': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def areas_requiring_reservation_view(request):
    """Obtener áreas que requieren reserva previa"""
    reservation_areas = CommonArea.objects.filter(
        requires_reservation=True,
        is_active=True,
        is_maintenance=False
    )
    
    serializer = CommonAreaSerializer(reservation_areas, many=True)
    
    return Response({
        'message': 'Áreas que requieren reserva previa',
        'count': reservation_areas.count(),
        'areas': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_area_availability_view(request, area_id):
    """Verificar si un área está abierta a una hora específica"""
    try:
        area = CommonArea.objects.get(id=area_id)
    except CommonArea.DoesNotExist:
        return Response({
            'error': 'Área común no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = CommonAreaAvailabilitySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    check_time = serializer.validated_data['check_time']
    is_open = area.is_open_at(check_time)
    
    return Response({
        'area': {
            'id': area.id,
            'name': area.name,
            'operating_hours': area.operating_hours
        },
        'check_time': check_time.strftime('%H:%M'),
        'is_open': is_open,
        'is_available': area.is_available,
        'message': f'El área {"está abierta" if is_open and area.is_available else "no está disponible"} a las {check_time.strftime("%H:%M")}'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_maintenance_view(request, area_id):
    """Activar/desactivar modo mantenimiento de un área"""
    try:
        area = CommonArea.objects.get(id=area_id)
    except CommonArea.DoesNotExist:
        return Response({
            'error': 'Área común no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Cambiar estado de mantenimiento
    area.is_maintenance = not area.is_maintenance
    area.save()
    
    status_text = "en mantenimiento" if area.is_maintenance else "disponible"
    
    response_serializer = CommonAreaSerializer(area)
    
    return Response({
        'message': f'Área "{area.name}" marcada como {status_text}',
        'area': response_serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_areas_view(request):
    """Buscar áreas comunes por nombre, tipo o ubicación"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response({
            'error': 'Parámetro de búsqueda "q" es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    areas = CommonArea.objects.filter(
        Q(name__icontains=query) |
        Q(location__icontains=query) |
        Q(area_type__icontains=query)
    )
    
    serializer = CommonAreaSerializer(areas, many=True)
    
    return Response({
        'query': query,
        'count': areas.count(),
        'areas': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def area_types_view(request):
    """Obtener todos los tipos de áreas disponibles"""
    types = [
        {
            'value': choice[0],
            'display': choice[1],
            'count': CommonArea.objects.filter(area_type=choice[0]).count()
        }
        for choice in CommonArea.AREA_TYPES
    ]
    
    return Response({
        'message': 'Tipos de áreas comunes disponibles',
        'types': types
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def common_area_stats_view(request):
    """Obtener estadísticas de áreas comunes"""
    total_areas = CommonArea.objects.count()
    
    stats = {
        'total_areas': total_areas,
        'available_areas': CommonArea.objects.filter(is_active=True, is_maintenance=False).count(),
        'maintenance_areas': CommonArea.objects.filter(is_maintenance=True).count(),
        'inactive_areas': CommonArea.objects.filter(is_active=False).count(),
        'reservation_required': CommonArea.objects.filter(requires_reservation=True).count(),
        'by_type': {}
    }
    
    # Contar por tipo
    for area_type, display_name in CommonArea.AREA_TYPES:
        count = CommonArea.objects.filter(area_type=area_type).count()
        stats['by_type'][area_type] = {
            'count': count,
            'display_name': display_name
        }
    
    return Response(stats)