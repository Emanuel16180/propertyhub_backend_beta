from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, ResidentProfile
from .serializers import (
    UserCreateSerializer, 
    UserDetailSerializer, 
    UserProfileSerializer,
    ResidentProfileSerializer
)

class UserListCreateView(generics.ListCreateAPIView):
    """Vista para listar todos los usuarios y crear nuevos"""
    queryset = User.objects.all().select_related('profile')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo usuario con validaciones"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Retornar el usuario creado con todos los datos
        response_serializer = UserDetailSerializer(user)
        
        return Response({
            'message': 'Usuario creado exitosamente',
            'user': response_serializer.data
        }, status=status.HTTP_201_CREATED)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar un usuario específico"""
    queryset = User.objects.all().select_related('profile')
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar usuario con mensaje personalizado"""
        instance = self.get_object()
        username = instance.username
        self.perform_destroy(instance)
        
        return Response({
            'message': f'Usuario {username} eliminado exitosamente'
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_by_type_view(request, user_type):
    """Obtener usuarios filtrados por tipo"""
    valid_types = ['admin', 'security', 'camera', 'resident']
    
    if user_type not in valid_types:
        return Response({
            'error': f'Tipo de usuario inválido. Tipos válidos: {", ".join(valid_types)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    users = User.objects.filter(
        profile__user_type=user_type
    ).select_related('profile')
    
    serializer = UserDetailSerializer(users, many=True)
    
    return Response({
        'user_type': user_type,
        'count': users.count(),
        'users': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def residents_detail_view(request):
    """Obtener todos los residentes con información detallada"""
    residents = User.objects.filter(
        profile__user_type='resident'
    ).select_related('profile__resident_info')
    
    users_data = []
    for user in residents:
        user_data = UserDetailSerializer(user).data
        
        # Agregar información de residente si existe
        if hasattr(user.profile, 'resident_info'):
            resident_data = ResidentProfileSerializer(user.profile.resident_info).data
            user_data['resident_details'] = resident_data
        
        users_data.append(user_data)
    
    return Response({
        'message': 'Residentes obtenidos exitosamente',
        'count': len(users_data),
        'residents': users_data
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile_view(request, user_id):
    """Actualizar perfil básico de usuario"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Actualizar datos del User
    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    user.email = request.data.get('email', user.email)
    user.save()
    
    # Actualizar datos del UserProfile
    if hasattr(user, 'profile'):
        user.profile.phone = request.data.get('phone', user.profile.phone)
        user.profile.save()
    
    serializer = UserDetailSerializer(user)
    
    return Response({
        'message': 'Perfil actualizado exitosamente',
        'user': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_resident_profile_view(request, user_id):
    """Crear o actualizar perfil de residente"""
    try:
        user = User.objects.get(id=user_id)
        if user.profile.user_type != 'resident':
            return Response({
                'error': 'El usuario debe ser de tipo residente'
            }, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Crear o actualizar ResidentProfile
    resident_profile, created = ResidentProfile.objects.get_or_create(
        user_profile=user.profile,
        defaults={
            'resident_type': request.data.get('resident_type'),
            'birth_date': request.data.get('birth_date'),
            'house_identifier': request.data.get('house_identifier', '')
        }
    )
    
    if not created:
        # Actualizar si ya existe
        resident_profile.resident_type = request.data.get('resident_type', resident_profile.resident_type)
        resident_profile.birth_date = request.data.get('birth_date', resident_profile.birth_date)
        resident_profile.house_identifier = request.data.get('house_identifier', resident_profile.house_identifier)
        resident_profile.save()
    
    serializer = ResidentProfileSerializer(resident_profile)
    
    return Response({
        'message': 'Perfil de residente actualizado exitosamente',
        'resident_profile': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_house_to_resident_view(request, user_id):
    """Asignar casa a un residente"""
    try:
        user = User.objects.get(id=user_id)
        if user.profile.user_type != 'resident':
            return Response({
                'error': 'El usuario debe ser de tipo residente'
            }, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    property_id = request.data.get('property_id')
    relationship = request.data.get('relationship', 'resident')
    is_primary = request.data.get('is_primary_resident', False)
    
    if not property_id:
        return Response({
            'error': 'property_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from apps.properties.models import Property, PropertyResident
        property_obj = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return Response({
            'error': 'Propiedad no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar si el residente ya tiene una casa asignada
    existing_assignment = PropertyResident.objects.filter(
        resident=user, is_active=True
    ).first()
    
    if existing_assignment:
        return Response({
            'error': f'El residente ya está asignado a la propiedad {existing_assignment.property.full_identifier}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Crear asignación
    property_resident = PropertyResident.objects.create(
        property=property_obj,
        resident=user,
        relationship=relationship,
        is_primary_resident=is_primary
    )
    
    # Actualizar el identificador en el perfil del residente
    if hasattr(user.profile, 'resident_info'):
        user.profile.resident_info.house_identifier = property_obj.full_identifier
        user.profile.resident_info.save()
    
    return Response({
        'message': f'Casa {property_obj.full_identifier} asignada exitosamente a {user.get_full_name()}',
        'assignment': {
            'user_id': user.id,
            'user_name': user.get_full_name(),
            'property_id': property_obj.id,
            'property_identifier': property_obj.full_identifier,
            'relationship': relationship,
            'is_primary_resident': is_primary
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_house_from_resident_view(request, user_id):
    """Remover casa de un residente"""
    try:
        user = User.objects.get(id=user_id)
        if user.profile.user_type != 'resident':
            return Response({
                'error': 'El usuario debe ser de tipo residente'
            }, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    from apps.properties.models import PropertyResident
    
    # Buscar asignación activa
    assignment = PropertyResident.objects.filter(
        resident=user, is_active=True
    ).first()
    
    if not assignment:
        return Response({
            'error': 'El residente no tiene casa asignada'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    property_identifier = assignment.property.full_identifier
    
    # Desactivar asignación
    assignment.is_active = False
    assignment.move_out_date = timezone.now().date()
    assignment.save()
    
    # Limpiar identificador en el perfil
    if hasattr(user.profile, 'resident_info'):
        user.profile.resident_info.house_identifier = ''
        user.profile.resident_info.save()
    
    return Response({
        'message': f'Casa {property_identifier} removida exitosamente de {user.get_full_name()}'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def residents_without_house_view(request):
    """Listar residentes que no tienen casa asignada"""
    from apps.properties.models import PropertyResident
    
    # Obtener residentes que no tienen asignación activa
    assigned_resident_ids = PropertyResident.objects.filter(
        is_active=True
    ).values_list('resident_id', flat=True)
    
    residents_without_house = User.objects.filter(
        profile__user_type='resident'
    ).exclude(
        id__in=assigned_resident_ids
    ).select_related('profile__resident_info')
    
    users_data = []
    for user in residents_without_house:
        user_data = UserDetailSerializer(user).data
        users_data.append(user_data)
    
    return Response({
        'message': 'Residentes sin casa asignada',
        'count': len(users_data),
        'residents': users_data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def residents_with_house_view(request):
    """Listar residentes que tienen casa asignada"""
    from apps.properties.models import PropertyResident
    
    assignments = PropertyResident.objects.filter(
        is_active=True
    ).select_related('resident', 'property', 'resident__profile')
    
    residents_data = []
    for assignment in assignments:
        user_data = UserDetailSerializer(assignment.resident).data
        user_data['house_assignment'] = {
            'property_id': assignment.property.id,
            'property_identifier': assignment.property.full_identifier,
            'relationship': assignment.relationship,
            'is_primary_resident': assignment.is_primary_resident,
            'move_in_date': assignment.move_in_date
        }
        residents_data.append(user_data)
    
    return Response({
        'message': 'Residentes con casa asignada',
        'count': len(residents_data),
        'residents': residents_data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_resident_photo_view(request, user_id):
    """Subir o actualizar foto de residente"""
    try:
        user = User.objects.get(id=user_id)
        if user.profile.user_type != 'resident':
            return Response({
                'error': 'El usuario debe ser de tipo residente'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not hasattr(user.profile, 'resident_info'):
            return Response({
                'error': 'El usuario no tiene perfil de residente creado'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except User.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    face_photo = request.FILES.get('face_photo')
    if not face_photo:
        return Response({
            'error': 'Debe enviar una imagen en el campo face_photo'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Actualizar la foto
    resident_profile = user.profile.resident_info
    resident_profile.face_photo = face_photo
    resident_profile.save()
    
    serializer = ResidentProfileSerializer(resident_profile)
    
    return Response({
        'message': 'Foto actualizada exitosamente',
        'resident_profile': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats_view(request):
    """Obtener estadísticas de usuarios"""
    total_users = User.objects.count()
    
    stats = {
        'total_users': total_users,
        'by_type': {},
        'residents_by_type': {}
    }
    
    # Contar por tipo de usuario
    for user_type, display_name in UserProfile.USER_TYPES:
        count = UserProfile.objects.filter(user_type=user_type).count()
        stats['by_type'][user_type] = {
            'count': count,
            'display_name': display_name
        }
    
    # Contar residentes por tipo
    for resident_type, display_name in ResidentProfile.RESIDENT_TYPES:
        count = ResidentProfile.objects.filter(resident_type=resident_type).count()
        stats['residents_by_type'][resident_type] = {
            'count': count,
            'display_name': display_name
        }
    
    return Response(stats)