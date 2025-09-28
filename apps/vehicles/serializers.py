from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Vehicle

class VehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear vehículos"""
    
    owner_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'license_plate', 'brand', 'model', 'year', 'color', 
            'vehicle_type', 'owner_id', 'parking_space', 'observations'
        ]
    
    def validate_owner_id(self, value):
        """Validar que el propietario existe y es residente"""
        try:
            user = User.objects.get(id=value)
            if not hasattr(user, 'profile') or user.profile.user_type != 'resident':
                raise serializers.ValidationError("El propietario debe ser un residente")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado")
    
    def validate_license_plate(self, value):
        """Validar formato de placa y unicidad"""
        if len(value) < 3:
            raise serializers.ValidationError("La placa debe tener al menos 3 caracteres")
        return value.upper()  # Convertir a mayúsculas
    
    def validate_year(self, value):
        """Validar que el año sea razonable"""
        import datetime
        current_year = datetime.datetime.now().year
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(f"El año debe estar entre 1900 y {current_year + 1}")
        return value
    
    def create(self, validated_data):
        """Crear vehículo con el propietario"""
        owner_id = validated_data.pop('owner_id')
        owner = User.objects.get(id=owner_id)
        vehicle = Vehicle.objects.create(owner=owner, **validated_data)
        return vehicle

class VehicleSerializer(serializers.ModelSerializer):
    """Serializer completo para mostrar vehículos"""
    
    owner_name = serializers.ReadOnlyField()
    owner_house = serializers.ReadOnlyField()
    vehicle_info = serializers.ReadOnlyField()
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)
    
    owner_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'license_plate', 'brand', 'model', 'year', 'color',
            'vehicle_type', 'vehicle_type_display', 'parking_space', 'observations',
            'owner', 'owner_name', 'owner_house', 'owner_details', 'vehicle_info',
            'is_active', 'created_at', 'updated_at'
        ]
    
    def get_owner_details(self, obj):
        """Obtener detalles del propietario"""
        return {
            'id': obj.owner.id,
            'name': obj.owner.get_full_name(),
            'email': obj.owner.email,
            'house': obj.owner_house
        }

class VehicleUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar vehículos"""
    
    class Meta:
        model = Vehicle
        fields = [
            'brand', 'model', 'year', 'color', 'vehicle_type',
            'parking_space', 'observations', 'is_active'
        ]
    
    def validate_year(self, value):
        """Validar que el año sea razonable"""
        import datetime
        current_year = datetime.datetime.now().year
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(f"El año debe estar entre 1900 y {current_year + 1}")
        return value

class ResidentForVehicleSerializer(serializers.ModelSerializer):
    """Serializer para mostrar residentes disponibles para asignar vehículos"""
    
    house_info = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'house_info']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_house_info(self, obj):
        """Obtener información de la casa del residente"""
        if hasattr(obj.profile, 'resident_info'):
            house_id = obj.profile.resident_info.house_identifier
            if house_id:
                return house_id
        return "Sin casa asignada"

class ChangeVehicleOwnerSerializer(serializers.Serializer):
    """Serializer para cambiar el propietario de un vehículo"""
    
    new_owner_id = serializers.IntegerField()
    
    def validate_new_owner_id(self, value):
        """Validar que el nuevo propietario existe y es residente"""
        try:
            user = User.objects.get(id=value)
            if not hasattr(user, 'profile') or user.profile.user_type != 'resident':
                raise serializers.ValidationError("El nuevo propietario debe ser un residente")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado")