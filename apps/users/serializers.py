from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, ResidentProfile

class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User de Django"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para UserProfile"""
    
    user = UserSerializer(read_only=True)
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'user_type', 'user_type_display', 'phone', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ResidentProfileSerializer(serializers.ModelSerializer):
    """Serializer para ResidentProfile"""
    
    user_profile = UserProfileSerializer(read_only=True)
    resident_type_display = serializers.CharField(source='get_resident_type_display', read_only=True)
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = ResidentProfile
        fields = [
            'id', 'user_profile', 'resident_type', 'resident_type_display', 
            'birth_date', 'age', 'face_photo', 'house_identifier', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios completos"""
    
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=UserProfile.USER_TYPES)
    phone = serializers.CharField(required=False, allow_blank=True)
    
    # Campos específicos para residentes (opcionales)
    resident_type = serializers.ChoiceField(choices=ResidentProfile.RESIDENT_TYPES, required=False)
    birth_date = serializers.DateField(required=False)
    house_identifier = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'user_type', 'phone', 'resident_type', 'birth_date', 'house_identifier'
        ]
    
    def validate(self, attrs):
        """Validaciones personalizadas"""
        user_type = attrs.get('user_type')
        
        # Si es residente, validar campos requeridos
        if user_type == 'resident':
            if not attrs.get('resident_type'):
                raise serializers.ValidationError("resident_type es requerido para residentes")
            if not attrs.get('birth_date'):
                raise serializers.ValidationError("birth_date es requerido para residentes")
        
        return attrs
    
    def create(self, validated_data):
        """Crear usuario con perfil"""
        # Extraer datos del perfil
        user_type = validated_data.pop('user_type')
        phone = validated_data.pop('phone', '')
        resident_type = validated_data.pop('resident_type', None)
        birth_date = validated_data.pop('birth_date', None)
        house_identifier = validated_data.pop('house_identifier', '')
        
        # Crear usuario
        user = User.objects.create_user(**validated_data)
        
        # Crear perfil
        user_profile = UserProfile.objects.create(
            user=user,
            user_type=user_type,
            phone=phone
        )
        
        # Si es residente, crear perfil de residente
        if user_type == 'resident' and resident_type and birth_date:
            ResidentProfile.objects.create(
                user_profile=user_profile,
                resident_type=resident_type,
                birth_date=birth_date,
                house_identifier=house_identifier
            )
        
        return user

class AssignHouseSerializer(serializers.Serializer):
    """Serializer para asignar casa a residente"""
    
    property_id = serializers.IntegerField()
    relationship = serializers.CharField(max_length=50, default='resident')
    is_primary_resident = serializers.BooleanField(default=False)
    
    def validate_property_id(self, value):
        """Validar que la propiedad existe"""
        try:
            from apps.properties.models import Property
            Property.objects.get(id=value)
            return value
        except Property.DoesNotExist:
            raise serializers.ValidationError("Propiedad no encontrada")

class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para mostrar detalles del usuario"""
    
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'profile']