from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Vehicle
from .serializers import (
    VehicleCreateSerializer,
    VehicleSerializer,
    VehicleUpdateSerializer,
    ResidentForVehicleSerializer,
    ChangeVehicleOwnerSerializer
)

class VehicleListCreateView(generics.ListCreateAPIView):
    """Vista para listar todos los vehículos y crear nuevos"""
    queryset = Vehicle.objects.all().select_related('owner')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VehicleCreateSerializer
        return VehicleSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo vehículo"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = serializer.save()
        
        # Retornar el vehículo creado con datos completos
        response_serializer = VehicleSerializer(vehicle)
        
        return Response({
            'message': 'Vehículo registrado exitosamente',
            'vehicle': response_serializer.data
        }, status=status.HTTP_201_CREATED)

class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar un vehículo específico"""
    queryset = Vehicle.objects.all().select_related('owner')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return VehicleUpdateSerializer
        return VehicleSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar vehículo con mensaje personalizado"""
        instance = self.get_object()
        license_plate = instance.license_plate
        self.perform_destroy(instance)
        
        return Response({
            'message': f'Vehículo {license_plate} eliminado exitosamente'
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def residents_for_vehicles_view(request):
    """Obtener lista de residentes disponibles para asignar vehículos"""
    # Obtener residentes con sus casas
    residents = User.objects.filter(
        profile__user_type='resident'
    ).select_related('profile__resident_info')
    
    residents_data = []
    for resident in residents:
        house_number = 'Sin casa'
        
        # Obtener solo el número de la casa si existe
        if hasattr(resident.profile, 'resident_info'):
            house_id = resident.profile.resident_info.house_identifier
            if house_id:
                # Extraer solo el número de casa del identificador completo
                import re
                # Buscar todos los números en el string
                numbers = re.findall(r'\d+', house_id)
                if numbers:
                    # Tomar el primer número encontrado (que debería ser el número de casa)
                    house_number = numbers[0]
                else:
                    house_number = house_id.strip()
        
        residents_data.append({
            'full_name': resident.get_full_name(),
            'house_info': house_number
        })
    
    return Response({
        'count': len(residents_data),
        'residents': residents_data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vehicles_by_type_view(request, vehicle_type):
    """Obtener vehículos filtrados por tipo"""
    valid_types = ['light', 'heavy', 'motorcycle']
    
    if vehicle_type not in valid_types:
        return Response({
            'error': f'Tipo de vehículo inválido. Tipos válidos: {", ".join(valid_types)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    vehicles = Vehicle.objects.filter(
        vehicle_type=vehicle_type, is_active=True
    ).select_related('owner')
    
    serializer = VehicleSerializer(vehicles, many=True)
    
    type_display = dict(Vehicle.VEHICLE_TYPES)[vehicle_type]
    
    return Response({
        'vehicle_type': vehicle_type,
        'type_display': type_display,
        'count': vehicles.count(),
        'vehicles': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vehicles_by_resident_view(request, resident_id):
    """Obtener todos los vehículos de un residente específico"""
    try:
        resident = User.objects.get(id=resident_id)
        if resident.profile.user_type != 'resident':
            return Response({
                'error': 'El usuario debe ser de tipo residente'
            }, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({
            'error': 'Residente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    vehicles = Vehicle.objects.filter(
        owner=resident, is_active=True
    )
    
    serializer = VehicleSerializer(vehicles, many=True)
    
    return Response({
        'resident': {
            'id': resident.id,
            'name': resident.get_full_name(),
            'house': getattr(resident.profile.resident_info, 'house_identifier', 'Sin casa') if hasattr(resident.profile, 'resident_info') else 'Sin casa'
        },
        'vehicle_count': vehicles.count(),
        'vehicles': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_vehicle_owner_view(request, vehicle_id):
    """Cambiar el propietario de un vehículo"""
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)
    except Vehicle.DoesNotExist:
        return Response({
            'error': 'Vehículo no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ChangeVehicleOwnerSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    new_owner_id = serializer.validated_data['new_owner_id']
    new_owner = User.objects.get(id=new_owner_id)
    
    old_owner_name = vehicle.owner.get_full_name()
    
    vehicle.owner = new_owner
    vehicle.save()
    
    response_serializer = VehicleSerializer(vehicle)
    
    return Response({
        'message': f'Propietario del vehículo {vehicle.license_plate} cambiado de {old_owner_name} a {new_owner.get_full_name()}',
        'vehicle': response_serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_vehicles_view(request):
    """Buscar vehículos por placa, marca, modelo o propietario"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response({
            'error': 'Parámetro de búsqueda "q" es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    vehicles = Vehicle.objects.filter(
        Q(license_plate__icontains=query) |
        Q(brand__icontains=query) |
        Q(model__icontains=query) |
        Q(owner__first_name__icontains=query) |
        Q(owner__last_name__icontains=query),
        is_active=True
    ).select_related('owner')
    
    serializer = VehicleSerializer(vehicles, many=True)
    
    return Response({
        'query': query,
        'count': vehicles.count(),
        'vehicles': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vehicle_stats_view(request):
    """Obtener estadísticas de vehículos"""
    total_vehicles = Vehicle.objects.filter(is_active=True).count()
    
    stats = {
        'total_vehicles': total_vehicles,
        'by_type': {},
        'active_vehicles': Vehicle.objects.filter(is_active=True).count(),
        'inactive_vehicles': Vehicle.objects.filter(is_active=False).count(),
    }
    
    # Contar por tipo
    for vehicle_type, display_name in Vehicle.VEHICLE_TYPES:
        count = Vehicle.objects.filter(vehicle_type=vehicle_type, is_active=True).count()
        stats['by_type'][vehicle_type] = {
            'count': count,
            'display_name': display_name
        }
    
    return Response(stats)