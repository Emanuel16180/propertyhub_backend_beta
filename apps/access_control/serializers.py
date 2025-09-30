# apps/access_control/serializers.py

from rest_framework import serializers
from .models import AccessLog
from django.contrib.auth.models import User

class AccessLogCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear un nuevo registro de acceso"""
    
    # El frontend enviará el ID del residente, que puede ser nulo
    resident_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = AccessLog
        fields = [
            'resident_id', 'confidence', 'is_authorized', 
            'main_message', 'detail_message', 'access_point'
        ]
        
    def validate_resident_id(self, value):
        """Validar que si se proporciona un ID, el usuario exista"""
        if value is not None:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("El ID de residente proporcionado no existe.")
        return value
        
    def create(self, validated_data):
        """Manejar la relación ForeignKey antes de guardar"""
        resident_id = validated_data.pop('resident_id', None)
        resident = User.objects.get(id=resident_id) if resident_id else None
        
        return AccessLog.objects.create(resident=resident, **validated_data)

class AccessLogSerializer(serializers.ModelSerializer):
    """Serializer completo para listar/detallar registros de acceso"""
    
    resident_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AccessLog
        fields = [
            'id', 'resident', 'resident_name', 'access_time', 'confidence', 
            'is_authorized', 'main_message', 'detail_message', 'access_point'
        ]
        read_only_fields = ['resident', 'access_time']
        
    def get_resident_name(self, obj):
        return obj.resident.get_full_name() if obj.resident else "Desconocido"