# apps/reservations/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, date, time
from .models import Reservation, ReservationStatus
from apps.common_areas.models import CommonArea
from apps.properties.models import Property, PropertyResident
from apps.users.models import UserProfile

class CommonAreaForReservationSerializer(serializers.ModelSerializer):
    """Serializer para áreas comunes en reservas"""
    area_type_display = serializers.CharField(source='get_area_type_display', read_only=True)
    operating_hours = serializers.SerializerMethodField()
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = CommonArea
        fields = ['id', 'name', 'area_type_display', 'capacity', 'operating_hours', 'requires_reservation', 'is_available']
    
    def get_operating_hours(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"

class PropertyForReservationSerializer(serializers.ModelSerializer):
    """Serializer para propiedades en reservas"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = ['id', 'house_number', 'block', 'display_name']
    
    def get_display_name(self, obj):
        return f"{obj.house_number} - Bloque {obj.block}"

class ResidentForReservationSerializer(serializers.ModelSerializer):
    """Serializer para residentes en reservas"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'display_name']
    
    def get_display_name(self, obj):
        return obj.get_full_name()

class ReservationSerializer(serializers.ModelSerializer):
    """Serializer completo para mostrar reservas"""
    common_area = CommonAreaForReservationSerializer(read_only=True)
    house_property = PropertyForReservationSerializer(read_only=True)
    resident = ResidentForReservationSerializer(read_only=True)
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    # Propiedades calculadas
    duration_hours = serializers.ReadOnlyField()
    resident_name = serializers.ReadOnlyField()
    property_identifier = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'common_area', 'house_property', 'resident', 'date', 
            'start_time', 'end_time', 'notes', 'status', 'status_display',
            'created_by_name', 'created_at', 'updated_at',
            'duration_hours', 'resident_name', 'property_identifier',
            'can_be_cancelled'
        ]

class CreateReservationSerializer(serializers.ModelSerializer):
    """Serializer para crear nuevas reservas"""
    common_area_id = serializers.IntegerField(write_only=True)
    property_id = serializers.IntegerField(write_only=True)
    resident_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'common_area_id', 'property_id', 'resident_id', 
            'date', 'start_time', 'end_time', 'notes'
        ]
    
    def validate_date(self, value):
        """Validar que la fecha no sea en el pasado"""
        if value < date.today():
            raise serializers.ValidationError("No se pueden hacer reservas para fechas pasadas.")
        return value
    
    def validate_common_area_id(self, value):
        """Validar que el área común existe y está disponible"""
        try:
            area = CommonArea.objects.get(id=value)
            if not area.is_available:
                raise serializers.ValidationError("El área común no está disponible.")
            return value
        except CommonArea.DoesNotExist:
            raise serializers.ValidationError("El área común no existe.")
    
    def validate_property_id(self, value):
        """Validar que la propiedad existe"""
        try:
            Property.objects.get(id=value)
            return value
        except Property.DoesNotExist:
            raise serializers.ValidationError("La propiedad no existe.")
    
    def validate_resident_id(self, value):
        """Validar que el residente existe"""
        try:
            user = User.objects.get(id=value)
            if not hasattr(user, 'profile') or user.profile.user_type != 'resident':
                raise serializers.ValidationError("El usuario debe ser un residente.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("El residente no existe.")
    
    def validate(self, data):
        """Validaciones cruzadas"""
        # Validar horarios
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError({
                'end_time': 'La hora de fin debe ser posterior a la hora de inicio.'
            })
        
        # Obtener objetos para validaciones
        common_area = CommonArea.objects.get(id=data['common_area_id'])
        property_obj = Property.objects.get(id=data['property_id'])
        resident = User.objects.get(id=data['resident_id'])
        
        # Validar horario del área común
        if (data['start_time'] < common_area.start_time or 
            data['end_time'] > common_area.end_time):
            raise serializers.ValidationError({
                'start_time': f'El horario debe estar entre {common_area.start_time} y {common_area.end_time}.'
            })
        
        # Validar que el residente pertenece a la propiedad
        is_owner = property_obj.owner == resident
        is_resident = PropertyResident.objects.filter(
            property=property_obj,
            resident=resident,
            is_active=True
        ).exists()
        
        if not (is_owner or is_resident):
            raise serializers.ValidationError({
                'resident_id': 'El residente seleccionado no pertenece a la propiedad indicada.'
            })
        
        # Validar que no haya conflictos de horario
        overlapping_reservations = Reservation.objects.filter(
            common_area_id=data['common_area_id'],
            date=data['date'],
            status='confirmed'
        ).filter(
            start_time__lt=data['end_time'],
            end_time__gt=data['start_time']
        )
        
        if overlapping_reservations.exists():
            raise serializers.ValidationError({
                'start_time': 'Ya existe una reserva confirmada para este horario.'
            })
        
        return data
    
    def create(self, validated_data):
        """Crear la reserva"""
        # Extraer IDs y obtener objetos
        common_area_id = validated_data.pop('common_area_id')
        property_id = validated_data.pop('property_id')
        resident_id = validated_data.pop('resident_id')
        
        common_area = CommonArea.objects.get(id=common_area_id)
        property_obj = Property.objects.get(id=property_id)
        resident = User.objects.get(id=resident_id)
        
        # Crear la reserva
        reservation = Reservation.objects.create(
            common_area=common_area,
            house_property=property_obj,
            resident=resident,
            created_by=self.context['request'].user,
            **validated_data
        )
        
        return reservation

class AvailableTimeSlotsSerializer(serializers.Serializer):
    """Serializer para consultar horarios disponibles"""
    common_area_id = serializers.IntegerField()
    date = serializers.DateField()
    
    def validate_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("No se pueden consultar horarios para fechas pasadas.")
        return value
    
    def validate_common_area_id(self, value):
        try:
            CommonArea.objects.get(id=value)
            return value
        except CommonArea.DoesNotExist:
            raise serializers.ValidationError("El área común no existe.")

class ResidentsByPropertySerializer(serializers.Serializer):
    """Serializer para obtener residentes de una propiedad"""
    property_id = serializers.IntegerField()
    
    def validate_property_id(self, value):
        try:
            Property.objects.get(id=value)
            return value
        except Property.DoesNotExist:
            raise serializers.ValidationError("La propiedad no existe.")

class ReservationUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar reservas"""
    
    class Meta:
        model = Reservation
        fields = ['notes', 'status']
    
    def validate_status(self, value):
        """Validar cambios de estado"""
        instance = self.instance
        
        if instance.status == 'completed':
            raise serializers.ValidationError("No se puede modificar una reserva completada.")
        
        if instance.status == 'cancelled' and value != 'cancelled':
            raise serializers.ValidationError("No se puede reactivar una reserva cancelada.")
        
        return value

class CancelReservationSerializer(serializers.Serializer):
    """Serializer para cancelar reservas"""
    reason = serializers.CharField(max_length=200, required=False, allow_blank=True)