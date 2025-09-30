# apps/visitor_control/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import VisitorLog, VisitVehicle, VisitReason, VehicleType
from apps.properties.models import Property
from apps.common_areas.models import CommonArea
from apps.users.serializers import UserSerializer # Reutilizamos UserSerializer

# --- Utilitarios para Dropdowns ---
class PropertyDestinationSerializer(serializers.ModelSerializer):
    """Serializer para mostrar Propiedades con propietario para el dropdown"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = ['id', 'full_identifier', 'owner_name', 'display_name']
        
    def get_display_name(self, obj):
        owner_name = obj.owner.get_full_name() if obj.owner else "Sin asignar"
        return f"Casa {obj.house_number} - {owner_name}"

class CommonAreaDestinationSerializer(serializers.ModelSerializer):
    """Serializer para Áreas Comunes para el dropdown"""
    class Meta:
        model = CommonArea
        fields = ['id', 'name', 'area_type']

# --- Vehicle Serializer ---
class VisitVehicleSerializer(serializers.ModelSerializer):
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)
    
    class Meta:
        model = VisitVehicle
        fields = [
            'license_plate', 'color', 'model', 'vehicle_type', 
            'vehicle_type_display'
        ]

# --- Log Detail Serializer (Lectura) ---
class VisitorLogSerializer(serializers.ModelSerializer):
    vehicle = VisitVehicleSerializer(read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    destination_display = serializers.SerializerMethodField()
    registered_by_name = serializers.CharField(source='registered_by.get_full_name', read_only=True)
    
    class Meta:
        model = VisitorLog
        fields = [
            'id', 'full_name', 'document_id', 'reason', 'reason_display',
            'property_to_visit', 'common_area_to_visit', 'destination_display',
            'observations', 'check_in_time', 'check_out_time', 'is_active',
            'registered_by_name', 'vehicle', 'document_photo_front', 'document_photo_back'
        ]
        
    def get_destination_display(self, obj):
        return obj.get_destination_display()

# --- Create Log Serializer (Escritura) ---
class VisitVehicleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitVehicle
        fields = [
            'license_plate', 'color', 'model', 'vehicle_type'
        ]

class VisitorLogCreateSerializer(serializers.ModelSerializer):
    # Campos anidados para el vehículo
    vehicle = VisitVehicleCreateSerializer(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = VisitorLog
        fields = [
            'full_name', 'document_id', 'document_photo_front', 'document_photo_back',
            'reason', 'property_to_visit', 'common_area_to_visit', 
            'observations', 'vehicle'
        ]
    
    def validate(self, data):
        """Validar que solo un destino (Propiedad o Área Común) sea seleccionado"""
        property_id = data.get('property_to_visit')
        area_id = data.get('common_area_to_visit')
        
        # Permitir que ambos sean nulos (Ej. Servicio Técnico general)
        if property_id and area_id:
            raise serializers.ValidationError(
                "Solo se puede seleccionar un destino: Casa/Propiedad O Área Común, no ambos."
            )
        
        # Si no se selecciona destino, es válido, pero se podría añadir una regla de negocio aquí si fuera necesario
        
        return data

    def create(self, validated_data):
        # Separar data del vehículo
        vehicle_data = validated_data.pop('vehicle', None)
        
        # Asignar usuario que registra (viene del request context)
        validated_data['registered_by'] = self.context['request'].user
        
        # Crear el log de visita
        visitor_log = VisitorLog.objects.create(**validated_data)
        
        # Crear el vehículo si se proporcionó data
        if vehicle_data:
            VisitVehicle.objects.create(visitor_log=visitor_log, **vehicle_data)
            
        return visitor_log

# --- Update Log Serializer ---
class VisitorLogUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorLog
        fields = ['check_out_time', 'is_active', 'observations']