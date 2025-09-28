from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Property, PropertyResident
from .serializers import (
    PropertyCreateSerializer,
    PropertySerializer,
    PropertyUpdateSerializer,
    AssignOwnerSerializer,
    PropertyResidentSerializer,
    AddResidentToPropertySerializer,
    PropertyWithResidentsSerializer
)

class PropertyListCreateView(generics.ListCreateAPIView):
    """Vista para listar todas las propiedades y crear nuevas"""
    queryset = Property.objects.all().select_related('owner')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PropertyCreateSerializer
        return PropertySerializer
    
    def create(self, request, *args, **kwargs):
        """Crear nueva propiedad"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        property_obj = serializer.save()
        
        # Retornar la propiedad creada con datos completos
        response_serializer = PropertySerializer(property_obj)
        
        return Response({
            'message': 'Propiedad creada exitosamente',
            'property': response_serializer.data
        }, status=status.HTTP_201_CREATED)

class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar una propiedad específica"""
    queryset = Property.objects.all().select_related('owner')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PropertyUpdateSerializer
        return PropertySerializer
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar propiedad con validaciones"""
        instance = self.get_object()
        
        # Verificar si tiene propietario o residentes
        if instance.owner:
            return Response({
                'error': 'No se puede eliminar una propiedad que tiene propietario asignado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if instance.residents.filter(is_active=True).exists():
            return Response({
                'error': 'No se puede eliminar una propiedad que tiene residentes activos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        house_number = instance.house_number
        self.perform_destroy(instance)
        
        return Response({
            'message': f'Propiedad {house_number} eliminada exitosamente'
        }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_owner_view(request, property_id):
    """Asignar propietario a una propiedad"""
    try:
        property_obj = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return Response({
            'error': 'Propiedad no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AssignOwnerSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    owner_id = serializer.validated_data['owner_id']
    owner = User.objects.get(id=owner_id)
    
    # Verificar si el usuario ya tiene otra propiedad como propietario
    existing_property = Property.objects.filter(owner=owner).first()
    if existing_property:
        return Response({
            'error': f'El usuario ya es propietario de la propiedad {existing_property.full_identifier}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Asignar propietario
    property_obj.owner = owner
    property_obj.status = 'occupied'
    property_obj.save()
    
    # Actualizar el identificador de casa en el perfil del residente
    if hasattr(owner.profile, 'resident_info'):
        owner.profile.resident_info.house_identifier = property_obj.full_identifier
        owner.profile.resident_info.save()
    
    response_serializer = PropertySerializer(property_obj)
    
    return Response({
        'message': f'Propietario asignado exitosamente a {property_obj.full_identifier}',
        'property': response_serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_owner_view(request, property_id):
    """Remover propietario de una propiedad"""
    try:
        property_obj = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return Response({
            'error': 'Propiedad no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if not property_obj.owner:
        return Response({
            'error': 'La propiedad no tiene propietario asignado'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Limpiar identificador de casa en el perfil del residente
    if hasattr(property_obj.owner.profile, 'resident_info'):
        property_obj.owner.profile.resident_info.house_identifier = ''
        property_obj.owner.profile.resident_info.save()
    
    owner_name = property_obj.owner.get_full_name()
    property_obj.owner = None
    property_obj.status = 'available'
    property_obj.save()
    
    response_serializer = PropertySerializer(property_obj)
    
    return Response({
        'message': f'Propietario {owner_name} removido exitosamente',
        'property': response_serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def properties_by_status_view(request, status_type):
    """Obtener propiedades filtradas por estado"""
    valid_statuses = ['available', 'occupied', 'maintenance', 'reserved']
    
    if status_type not in valid_statuses:
        return Response({
            'error': f'Estado inválido. Estados válidos: {", ".join(valid_statuses)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    properties = Property.objects.filter(status=status_type).select_related('owner')
    serializer = PropertySerializer(properties, many=True)
    
    return Response({
        'status': status_type,
        'count': properties.count(),
        'properties': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def properties_with_residents_view(request):
    """Obtener todas las propiedades con información de residentes"""
    properties = Property.objects.all().select_related('owner').prefetch_related('residents__resident')
    serializer = PropertyWithResidentsSerializer(properties, many=True)
    
    return Response({
        'message': 'Propiedades con residentes obtenidas exitosamente',
        'count': properties.count(),
        'properties': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_resident_to_property_view(request, property_id):
    """Agregar residente a una propiedad"""
    try:
        property_obj = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return Response({
            'error': 'Propiedad no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AddResidentToPropertySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    resident_id = serializer.validated_data['resident_id']
    resident = User.objects.get(id=resident_id)
    
    # Verificar si el residente ya está en esta propiedad
    if PropertyResident.objects.filter(property=property_obj, resident=resident, is_active=True).exists():
        return Response({
            'error': 'El residente ya está asignado a esta propiedad'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Crear relación residente-propiedad
    property_resident = PropertyResident.objects.create(
        property=property_obj,
        resident=resident,
        relationship=serializer.validated_data['relationship'],
        is_primary_resident=serializer.validated_data.get('is_primary_resident', False),
        move_in_date=serializer.validated_data.get('move_in_date')
    )
    
    # Actualizar identificador de casa en el perfil del residente
    if hasattr(resident.profile, 'resident_info'):
        resident.profile.resident_info.house_identifier = property_obj.full_identifier
        resident.profile.resident_info.save()
    
    response_serializer = PropertyResidentSerializer(property_resident)
    
    return Response({
        'message': f'Residente agregado exitosamente a {property_obj.full_identifier}',
        'property_resident': response_serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def property_stats_view(request):
    """Obtener estadísticas de propiedades"""
    total_properties = Property.objects.count()
    
    stats = {
        'total_properties': total_properties,
        'by_status': {},
        'with_owner': Property.objects.filter(owner__isnull=False).count(),
        'without_owner': Property.objects.filter(owner__isnull=True).count(),
        'total_residents': PropertyResident.objects.filter(is_active=True).count()
    }
    
    # Contar por estado
    for status_code, status_name in Property.STATUS_CHOICES:
        count = Property.objects.filter(status=status_code).count()
        stats['by_status'][status_code] = {
            'count': count,
            'display_name': status_name
        }
    
    return Response(stats)