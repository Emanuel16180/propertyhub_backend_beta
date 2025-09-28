from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Property, PropertyResident
from apps.users.serializers import UserSerializer

class PropertyCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear propiedades (sin propietario inicialmente)"""
    
    class Meta:
        model = Property
        fields = [
            'house_number', 'block', 'floor', 'area_m2', 
            'bedrooms', 'bathrooms', 'parking_spaces', 
            'status', 'description'
        ]
    
    def validate_house_number(self, value):
        """Validar que el número de casa sea único"""
        if Property.objects.filter(house_number=value).exists():
            raise serializers.ValidationError("Ya existe una propiedad con este número de casa")
        return value

class PropertySerializer(serializers.ModelSerializer):
    """Serializer completo para mostrar propiedades"""
    
    owner = UserSerializer(read_only=True)
    owner_name = serializers.ReadOnlyField()
    full_identifier = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Property
        fields = [
            'id', 'house_number', 'block', 'floor', 'area_m2',
            'bedrooms', 'bathrooms', 'parking_spaces', 'status', 'status_display',
            'description', 'owner', 'owner_name', 'full_identifier', 
            'is_available', 'created_at', 'updated_at'
        ]

class PropertyUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar propiedades"""
    
    class Meta:
        model = Property
        fields = [
            'house_number', 'block', 'floor', 'area_m2',
            'bedrooms', 'bathrooms', 'parking_spaces', 
            'status', 'description'
        ]

class AssignOwnerSerializer(serializers.Serializer):
    """Serializer para asignar propietario a una propiedad"""
    
    owner_id = serializers.IntegerField()
    
    def validate_owner_id(self, value):
        """Validar que el usuario existe y es residente"""
        try:
            user = User.objects.get(id=value)
            if not hasattr(user, 'profile') or user.profile.user_type != 'resident':
                raise serializers.ValidationError("El usuario debe ser de tipo residente")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado")

class PropertyResidentSerializer(serializers.ModelSerializer):
    """Serializer para residentes de propiedades"""
    
    resident = UserSerializer(read_only=True)
    property_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyResident
        fields = [
            'id', 'property', 'resident', 'property_info', 'relationship',
            'is_primary_resident', 'move_in_date', 'move_out_date',
            'is_active', 'created_at', 'updated_at'
        ]
    
    def get_property_info(self, obj):
        return {
            'id': obj.property.id,
            'full_identifier': obj.property.full_identifier,
            'house_number': obj.property.house_number,
            'block': obj.property.block
        }

class AddResidentToPropertySerializer(serializers.Serializer):
    """Serializer para agregar residente a una propiedad"""
    
    resident_id = serializers.IntegerField()
    relationship = serializers.CharField(max_length=50)
    is_primary_resident = serializers.BooleanField(default=False)
    move_in_date = serializers.DateField(required=False)
    
    def validate_resident_id(self, value):
        """Validar que el usuario existe y es residente"""
        try:
            user = User.objects.get(id=value)
            if not hasattr(user, 'profile') or user.profile.user_type != 'resident':
                raise serializers.ValidationError("El usuario debe ser de tipo residente")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado")

class PropertyWithResidentsSerializer(serializers.ModelSerializer):
    """Serializer para mostrar propiedades con sus residentes"""
    
    owner = UserSerializer(read_only=True)
    residents = PropertyResidentSerializer(many=True, read_only=True)
    owner_name = serializers.ReadOnlyField()
    full_identifier = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_residents = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'house_number', 'block', 'floor', 'area_m2',
            'bedrooms', 'bathrooms', 'parking_spaces', 'status', 'status_display',
            'description', 'owner', 'owner_name', 'full_identifier',
            'residents', 'total_residents', 'created_at', 'updated_at'
        ]
    
    def get_total_residents(self, obj):
        return obj.residents.filter(is_active=True).count()