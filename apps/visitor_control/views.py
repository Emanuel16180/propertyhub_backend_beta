# apps/visitor_control/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from .models import VisitorLog, VisitVehicle, VisitReason, VehicleType
from .serializers import (
    VisitorLogCreateSerializer,
    VisitorLogSerializer,
    VisitorLogUpdateSerializer,
    PropertyDestinationSerializer,
    CommonAreaDestinationSerializer
)
from apps.properties.models import Property
from apps.common_areas.models import CommonArea

class VisitorLogListCreateView(generics.ListCreateAPIView):
    """
    GET: Lista los registros de visitantes
    POST: Registra un nuevo visitante
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtra por activo por defecto (visitantes DENTRO)
        queryset = VisitorLog.objects.filter(is_active=True).select_related(
            'property_to_visit', 
            'common_area_to_visit', 
            'vehicle', 
            'registered_by'
        )
        
        # Permite ver visitantes inactivos (ya salidos) con un query param
        if self.request.query_params.get('include_inactive') == 'true':
            queryset = VisitorLog.objects.all().select_related(
                'property_to_visit', 
                'common_area_to_visit', 
                'vehicle', 
                'registered_by'
            )
        
        # Filtrar por búsqueda
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(document_id__icontains=search) |
                Q(vehicle__license_plate__icontains=search)
            )
            
        return queryset.order_by('-check_in_time')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VisitorLogCreateSerializer
        return VisitorLogSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo registro de visitante"""
        # Se pasa el request.user en el contexto para asignar 'registered_by'
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        visitor_log = serializer.save()
        
        response_serializer = VisitorLogSerializer(visitor_log)
        
        return Response({
            'message': 'Visitante registrado exitosamente',
            'visitor_log': response_serializer.data
        }, status=status.HTTP_201_CREATED)

class VisitorLogDetailUpdateView(generics.RetrieveUpdateAPIView):
    """
    GET: Obtener detalles del registro
    PATCH: Actualizar el registro (principalmente para hacer CHECK-OUT)
    """
    queryset = VisitorLog.objects.all().select_related(
        'property_to_visit', 
        'common_area_to_visit', 
        'vehicle', 
        'registered_by'
    )
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        # Usar el serializer de actualización si es una petición de modificación
        if self.request.method in ['PUT', 'PATCH']:
            return VisitorLogUpdateSerializer
        return VisitorLogSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_out_visitor_view(request, log_id):
    """Realiza el check-out de un visitante activo"""
    try:
        visitor_log = VisitorLog.objects.get(id=log_id, is_active=True)
    except VisitorLog.DoesNotExist:
        return Response({
            'error': 'Registro de visitante activo no encontrado.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Realizar el Check-out
    visitor_log.is_active = False
    visitor_log.check_out_time = timezone.now()
    visitor_log.save()
    
    response_serializer = VisitorLogSerializer(visitor_log)
    
    return Response({
        'message': f'Check-out de {visitor_log.full_name} completado exitosamente',
        'visitor_log': response_serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_visitor_form_data(request):
    """Endpoint que retorna los datos necesarios para poblar el formulario de visitante"""
    
    # 1. Motivos de Visita
    reasons = [
        {'value': choice[0], 'display': choice[1]}
        for choice in VisitReason.choices
    ]
    
    # 2. Tipos de Vehículo
    vehicle_types = [
        {'value': choice[0], 'display': choice[1]}
        for choice in VehicleType.choices
    ]
    
    # 3. Lista de Casas/Propiedades (Casa + Propietario)
    properties = Property.objects.filter(
        status__in=['occupied', 'available'] # Solo casas que pueden ser visitadas
    ).select_related('owner').order_by('house_number')
    
    property_data = PropertyDestinationSerializer(properties, many=True).data
    
    # 4. Lista de Áreas Comunes (Disponibles)
    common_areas = CommonArea.objects.filter(
        is_active=True,
        is_maintenance=False
    ).order_by('name')
    
    common_area_data = CommonAreaDestinationSerializer(common_areas, many=True).data
    
    # Combinar la lista de destinos para el dropdown
    destinations = [
        {'type': 'area', 'id': area['id'], 'display_name': area['name']} 
        for area in common_area_data
    ] + [
        {'type': 'property', 'id': prop['id'], 'display_name': prop['display_name']} 
        for prop in property_data
    ]

    # Añadir un separador para la UI, si es necesario, o solo retornar las dos listas separadas
    
    return Response({
        'message': 'Datos del formulario obtenidos exitosamente',
        'reasons': reasons,
        'vehicle_types': vehicle_types,
        'properties': property_data,
        'common_areas': common_area_data,
        'all_destinations': destinations
    })