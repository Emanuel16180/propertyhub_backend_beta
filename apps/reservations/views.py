# apps/reservations/views.py
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from datetime import datetime, date, time, timedelta

from .models import Reservation
from .serializers import (
    ReservationSerializer,
    CreateReservationSerializer,
    AvailableTimeSlotsSerializer,
    ResidentsByPropertySerializer,
    ReservationUpdateSerializer,
    CancelReservationSerializer,
    CommonAreaForReservationSerializer,
    PropertyForReservationSerializer,
    ResidentForReservationSerializer
)
from apps.common_areas.models import CommonArea
from apps.properties.models import Property, PropertyResident
from apps.users.models import UserProfile

class ReservationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

class ReservationListCreateView(generics.ListCreateAPIView):
    """
    GET: Lista todas las reservas
    POST: Crea una nueva reserva
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ReservationPagination
    
    def get_queryset(self):
        queryset = Reservation.objects.select_related(
            'common_area', 'house_property', 'resident', 'created_by'
        ).prefetch_related('house_property__owner')
        
        # Filtros
        common_area_id = self.request.query_params.get('common_area_id')
        if common_area_id:
            queryset = queryset.filter(common_area_id=common_area_id)
        
        property_id = self.request.query_params.get('property_id')
        if property_id:
            queryset = queryset.filter(house_property_id=property_id)
        
        resident_id = self.request.query_params.get('resident_id')
        if resident_id:
            queryset = queryset.filter(resident_id=resident_id)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        date_filter = self.request.query_params.get('date')
        if date_filter:
            queryset = queryset.filter(date=date_filter)
        
        # Filtrar por usuario actual si no es admin
        if not self.request.user.is_staff:
            # Mostrar solo reservas del usuario o de sus propiedades
            user_properties = Property.objects.filter(
                Q(owner=self.request.user) |
                Q(residents__resident=self.request.user, residents__is_active=True)
            )
            queryset = queryset.filter(
                Q(resident=self.request.user) |
                Q(property__in=user_properties)
            )
        
        return queryset.order_by('-date', '-start_time')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateReservationSerializer
        return ReservationSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear nueva reserva"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = serializer.save()
        
        # Retornar la reserva creada con datos completos
        response_serializer = ReservationSerializer(reservation)
        
        return Response({
            'message': 'Reserva creada exitosamente',
            'reservation': response_serializer.data
        }, status=status.HTTP_201_CREATED)

class ReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Obtiene una reserva específica
    PUT/PATCH: Actualiza una reserva
    DELETE: Cancela una reserva
    """
    queryset = Reservation.objects.select_related(
        'common_area', 'house_property', 'resident', 'created_by'
    )
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ReservationUpdateSerializer
        return ReservationSerializer
    
    def get_object(self):
        """Verificar permisos para acceder a la reserva"""
        obj = super().get_object()
        
        # Solo el creador, el residente o admin pueden ver/modificar
        if (not self.request.user.is_staff and 
            obj.created_by != self.request.user and 
            obj.resident != self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permisos para acceder a esta reserva.")
        
        return obj
    
    def destroy(self, request, *args, **kwargs):
        """Cancelar reserva en lugar de eliminar"""
        reservation = self.get_object()
        
        if not reservation.can_be_cancelled:
            return Response({
                'error': 'Esta reserva no se puede cancelar.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reservation.status = 'cancelled'
        reservation.save()
        
        response_serializer = ReservationSerializer(reservation)
        
        return Response({
            'message': 'Reserva cancelada exitosamente',
            'reservation': response_serializer.data
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_common_areas_view(request):
    """Obtener áreas comunes disponibles para reservar"""
    areas = CommonArea.objects.filter(
        is_active=True,
        is_maintenance=False
        # Removemos el filtro requires_reservation=True
        # porque queremos mostrar TODAS las áreas disponibles
    )
    
    serializer = CommonAreaForReservationSerializer(areas, many=True)
    
    return Response({
        'message': 'Áreas comunes disponibles',
        'count': areas.count(),
        'areas': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_properties_view(request):
    """Obtener propiedades con propietarios o residentes"""
    # Propiedades que tienen propietario o residentes activos
    properties = Property.objects.filter(
        Q(owner__isnull=False) |
        Q(residents__is_active=True)
    ).distinct().select_related('owner')
    
    serializer = PropertyForReservationSerializer(properties, many=True)
    
    return Response({
        'message': 'Propiedades disponibles',
        'count': properties.count(),
        'properties': serializer.data
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def residents_by_property_view(request):
    """Obtener residentes de una propiedad específica"""
    serializer = ResidentsByPropertySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    property_id = serializer.validated_data['property_id']
    property_obj = Property.objects.get(id=property_id)
    
    # Obtener propietario y residentes
    residents = []
    
    # Agregar propietario si existe
    if property_obj.owner:
        residents.append(property_obj.owner)
    
    # Agregar residentes activos
    property_residents = PropertyResident.objects.filter(
        property=property_obj,
        is_active=True
    ).select_related('resident')
    
    for prop_resident in property_residents:
        if prop_resident.resident not in residents:
            residents.append(prop_resident.resident)
    
    # Serializar residentes
    resident_data = []
    for resident in residents:
        # Verificar que sea residente
        if hasattr(resident, 'profile') and resident.profile.user_type == 'resident':
            resident_data.append({
                'id': resident.id,
                'display_name': resident.get_full_name(),
                'is_owner': resident == property_obj.owner
            })
    
    return Response({
        'property': {
            'id': property_obj.id,
            'display_name': f"{property_obj.house_number} - Bloque {property_obj.block}"
        },
        'residents': resident_data
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def available_time_slots_view(request):
    """Obtener horarios disponibles para una fecha y área común"""
    serializer = AvailableTimeSlotsSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    common_area_id = serializer.validated_data['common_area_id']
    reservation_date = serializer.validated_data['date']
    
    common_area = CommonArea.objects.get(id=common_area_id)
    
    # Obtener horarios disponibles
    time_slots = Reservation.get_available_time_slots(common_area, reservation_date)
    
    return Response({
        'common_area': {
            'id': common_area.id,
            'name': common_area.name,
            'operating_hours': f"{common_area.start_time} - {common_area.end_time}"
        },
        'date': reservation_date,
        'time_slots': time_slots,
        'available_count': sum(1 for slot in time_slots if slot['available'])
    })

# Asegúrate de tener estos imports al inicio del archivo:
# from django.db.models import Q
# from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_reservations_view(request):
    """Obtener reservas del usuario actual (como residente o como dueño de la propiedad)"""
    user = request.user

    # 1. Identificar propiedades vinculadas al usuario (Dueño o Residente)
    user_properties = Property.objects.filter(
        Q(owner=user) |
        Q(residents__resident=user, residents__is_active=True)
    )

    # 2. Hacer una ÚNICA consulta con condiciones OR
    all_reservations = Reservation.objects.filter(
        Q(resident=user) | 
        Q(house_property__in=user_properties)
    ).select_related(
        'common_area', 
        'house_property', 
        'resident', 
        'created_by'
    ).order_by('-date', '-start_time').distinct()
    
    # 3. Serializar y responder
    serializer = ReservationSerializer(all_reservations, many=True)
    
    return Response({
        'message': 'Mis reservas',
        'count': all_reservations.count(),
        'reservations': serializer.data
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_reservation_view(request, reservation_id):
    """Cancelar una reserva específica"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Verificar permisos
    if (not request.user.is_staff and 
        reservation.created_by != request.user and 
        reservation.resident != request.user):
        return Response({
            'error': 'No tienes permisos para cancelar esta reserva.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if not reservation.can_be_cancelled:
        return Response({
            'error': 'Esta reserva no se puede cancelar.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = CancelReservationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    reservation.status = 'cancelled'
    reservation.notes = f"{reservation.notes}\nCancelada: {serializer.validated_data.get('reason', 'Sin motivo especificado')}"
    reservation.save()
    
    response_serializer = ReservationSerializer(reservation)
    
    return Response({
        'message': 'Reserva cancelada exitosamente',
        'reservation': response_serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reservations_by_area_view(request, area_id):
    """Obtener reservas de un área común específica"""
    try:
        common_area = CommonArea.objects.get(id=area_id)
    except CommonArea.DoesNotExist:
        return Response({
            'error': 'Área común no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Filtros opcionales
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    status_filter = request.query_params.get('status', 'confirmed')
    
    reservations = Reservation.objects.filter(
        common_area=common_area,
        status=status_filter
    ).select_related('house_property', 'resident')
    
    if date_from:
        reservations = reservations.filter(date__gte=date_from)
    
    if date_to:
        reservations = reservations.filter(date__lte=date_to)
    
    serializer = ReservationSerializer(reservations, many=True)
    
    return Response({
        'common_area': {
            'id': common_area.id,
            'name': common_area.name,
            'area_type_display': common_area.get_area_type_display()
        },
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
            'status': status_filter
        },
        'count': reservations.count(),
        'reservations': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reservations_by_date_view(request):
    """Obtener reservas de una fecha específica"""
    reservation_date = request.query_params.get('date')
    
    if not reservation_date:
        return Response({
            'error': 'Parámetro "date" es requerido (formato: YYYY-MM-DD)'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        date_obj = datetime.strptime(reservation_date, '%Y-%m-%d').date()
    except ValueError:
        return Response({
            'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    reservations = Reservation.objects.filter(
        date=date_obj,
        status='confirmed'
    ).select_related('common_area', 'house_property', 'resident').order_by('start_time')
    
    serializer = ReservationSerializer(reservations, many=True)
    
    return Response({
        'date': reservation_date,
        'count': reservations.count(),
        'reservations': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reservation_stats_view(request):
    """Obtener estadísticas de reservas"""
    from django.db.models import Count
    from datetime import timedelta
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'total_reservations': Reservation.objects.count(),
        'confirmed_reservations': Reservation.objects.filter(status='confirmed').count(),
        'pending_reservations': Reservation.objects.filter(status='pending').count(),
        'cancelled_reservations': Reservation.objects.filter(status='cancelled').count(),
        
        # Reservas por período
        'today_reservations': Reservation.objects.filter(date=today, status='confirmed').count(),
        'week_reservations': Reservation.objects.filter(date__gte=week_ago, status='confirmed').count(),
        'month_reservations': Reservation.objects.filter(date__gte=month_ago, status='confirmed').count(),
        
        # Próximas reservas
        'upcoming_reservations': Reservation.objects.filter(date__gte=today, status='confirmed').count(),
        
        # Por área común
        'by_area': {},
        
        # Por estado
        'by_status': {}
    }
    
    # Contar por área común
    area_stats = Reservation.objects.values(
        'common_area__name', 'common_area__area_type'
    ).annotate(count=Count('id'))
    
    for area_stat in area_stats:
        area_name = area_stat['common_area__name']
        stats['by_area'][area_name] = {
            'count': area_stat['count'],
            'area_type': area_stat['common_area__area_type']
        }
    
    # Contar por estado
    status_stats = Reservation.objects.values('status').annotate(count=Count('id'))
    for status_stat in status_stats:
        stats['by_status'][status_stat['status']] = status_stat['count']
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def upcoming_reservations_view(request):
    """Obtener próximas reservas (hoy y futuras)"""
    today = date.today()
    
    reservations = Reservation.objects.filter(
        date__gte=today,
        status='confirmed'
    ).select_related('common_area', 'house_property', 'resident').order_by('date', 'start_time')
    
    # Limitar a las próximas 20 reservas
    reservations = reservations[:20]
    
    serializer = ReservationSerializer(reservations, many=True)
    
    return Response({
        'message': 'Próximas reservas confirmadas',
        'count': reservations.count(),
        'reservations': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_availability_view(request):
    """Verificar disponibilidad rápida para múltiples fechas"""
    area_id = request.query_params.get('area_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not all([area_id, start_date, end_date]):
        return Response({
            'error': 'Parámetros requeridos: area_id, start_date, end_date'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        common_area = CommonArea.objects.get(id=area_id)
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except (CommonArea.DoesNotExist, ValueError):
        return Response({
            'error': 'Área común no encontrada o formato de fecha inválido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verificar disponibilidad por cada día
    availability = []
    current_date = start_date_obj
    
    while current_date <= end_date_obj:
        if current_date >= date.today():  # Solo fechas futuras
            time_slots = Reservation.get_available_time_slots(common_area, current_date)
            available_slots = sum(1 for slot in time_slots if slot['available'])
            total_slots = len(time_slots)
            
            availability.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'available_slots': available_slots,
                'total_slots': total_slots,
                'is_fully_booked': available_slots == 0,
                'availability_percentage': (available_slots / total_slots * 100) if total_slots > 0 else 0
            })
        
        current_date += timedelta(days=1)
    
    return Response({
        'common_area': {
            'id': common_area.id,
            'name': common_area.name
        },
        'date_range': {
            'start': start_date,
            'end': end_date
        },
        'availability': availability
    })