# apps/communications/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Communication, CommunicationRead

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class CommunicationSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    communication_type_display = serializers.CharField(source='get_communication_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    target_audience_display = serializers.CharField(source='get_target_audience_display', read_only=True)
    read_count = serializers.SerializerMethodField()
    is_read_by_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Communication
        fields = [
            'id', 'title', 'message', 'communication_type', 'communication_type_display',
            'priority', 'priority_display', 'target_audience', 'target_audience_display',
            'author', 'author_name', 'created_at', 'updated_at', 'published_at',
            'expires_at', 'is_active', 'attachments', 'read_count', 'is_read_by_user'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at', 'published_at']
    
    def get_read_count(self, obj):
        return obj.read_by.count()
    
    def get_is_read_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.read_by.filter(user=request.user).exists()
        return False

class CreateCommunicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Communication
        fields = [
            'title', 'message', 'communication_type', 'priority', 
            'target_audience', 'expires_at', 'attachments'
        ]
    
    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "El título debe tener al menos 5 caracteres."
            )
        return value.strip()
    
    def validate_message(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "El mensaje debe tener al menos 10 caracteres."
            )
        return value.strip()

class CommunicationReadSerializer(serializers.ModelSerializer):
    communication_title = serializers.CharField(source='communication.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = CommunicationRead
        fields = ['id', 'communication', 'communication_title', 'user', 'user_name', 'read_at']
        read_only_fields = ['user', 'read_at']