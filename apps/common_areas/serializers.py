from rest_framework import serializers
from .models import CommonArea
from datetime import time

class CommonAreaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear áreas comunes"""
    
    class Meta:
        model = CommonArea
        fields = [
            'name', 'area_type', 'location', 'capacity',
            'start_time', 'end_time', 'requires_reservation',
            'usage_rules', 'description'
        ]
    
    def validate_capacity(self, value):
        """Validar que la capacidad sea razonable"""
        if value <= 0:
            raise serializers.ValidationError("La capacidad debe ser mayor a 0")
        if value > 1000:
            raise serializers.ValidationError("La capacidad no puede ser mayor a 1000 personas")
        return value
    
    def validate(self, attrs):
        """Validar que la hora de inicio sea menor a la hora de fin"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        # Permitir horarios que cruzan medianoche (ej: 22:00 - 06:00)
        # Solo validar que no sean iguales
        if start_time == end_time:
            raise serializers.ValidationError("La hora de inicio y fin no pueden ser iguales")
        
        return attrs

class CommonAreaSerializer(serializers.ModelSerializer):
    """Serializer completo para mostrar áreas comunes"""
    
    area_type_display = serializers.CharField(source='get_area_type_display', read_only=True)
    is_available = serializers.ReadOnlyField()
    operating_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = CommonArea
        fields = [
            'id', 'name', 'area_type', 'area_type_display', 'location',
            'capacity', 'start_time', 'end_time', 'operating_hours',
            'requires_reservation', 'usage_rules', 'description',
            'is_active', 'is_maintenance', 'is_available',
            'created_at', 'updated_at'
        ]

class CommonAreaUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar áreas comunes"""
    
    class Meta:
        model = CommonArea
        fields = [
            'name', 'location', 'capacity', 'start_time', 'end_time',
            'requires_reservation', 'usage_rules', 'description',
            'is_active', 'is_maintenance'
        ]
    
    def validate_capacity(self, value):
        """Validar que la capacidad sea razonable"""
        if value <= 0:
            raise serializers.ValidationError("La capacidad debe ser mayor a 0")
        if value > 1000:
            raise serializers.ValidationError("La capacidad no puede ser mayor a 1000 personas")
        return value
    
    def validate(self, attrs):
        """Validar horarios"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if start_time and end_time and start_time == end_time:
            raise serializers.ValidationError("La hora de inicio y fin no pueden ser iguales")
        
        return attrs

class CommonAreaSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para listados básicos"""
    
    area_type_display = serializers.CharField(source='get_area_type_display', read_only=True)
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = CommonArea
        fields = ['id', 'name', 'area_type_display', 'location', 'is_available']

class CommonAreaAvailabilitySerializer(serializers.Serializer):
    """Serializer para verificar disponibilidad de área común"""
    
    check_time = serializers.TimeField()
    
    def validate_check_time(self, value):
        """Validar formato de hora"""
        return value