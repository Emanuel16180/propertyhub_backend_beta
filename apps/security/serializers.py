# apps/security/serializers.py

from rest_framework import serializers
from .models import IntrusionLog
from django.contrib.auth.models import User

class IntrusionLogSerializer(serializers.ModelSerializer):
    """Serializer para listar y obtener detalles de los registros de intrusión."""
    
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    
    class Meta:
        model = IntrusionLog
        fields = [
            'id', 'message', 'confidence', 'detection_time', 
            'camera_identifier', 'is_resolved', 'resolved_by', 
            'resolved_by_name'
        ]
        read_only_fields = ['detection_time', 'resolved_by', 'resolved_by_name']

class IntrusionLogCreateSerializer(serializers.ModelSerializer):
    """Serializer para la creación rápida de un registro de intrusión."""
    class Meta:
        model = IntrusionLog
        fields = [
            'message', 'confidence', 'camera_identifier'
        ]
    
    def validate_message(self, value):
        if not value:
            raise serializers.ValidationError("El mensaje de la alerta es obligatorio.")
        return value

class IntrusionLogUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar un registro (ej. marcar como resuelto)."""
    class Meta:
        model = IntrusionLog
        fields = [
            'is_resolved', 'resolved_by' # resolved_by será llenado en la vista
        ]