from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from apps.users.serializers import UserDetailSerializer

class LoginView(generics.GenericAPIView):
    """Vista para login con username y password"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username y password son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Autenticar usuario
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'error': 'Usuario desactivado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generar tokens
        refresh = RefreshToken.for_user(user)
        
        # Serializar datos del usuario
        user_data = UserDetailSerializer(user).data
        
        return Response({
            'message': 'Login exitoso',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': user_data
        }, status=status.HTTP_200_OK)

class LogoutView(generics.GenericAPIView):
    """Vista para logout - blacklist del refresh token"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            
            if not refresh_token:
                return Response({
                    'error': 'refresh_token es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Blacklist del token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Logout exitoso'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """Vista para renovar access token"""
    refresh_token = request.data.get('refresh_token')
    
    if not refresh_token:
        return Response({
            'error': 'refresh_token es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        return Response({
            'access_token': access_token
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Token inválido o expirado'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """Vista para obtener perfil del usuario actual"""
    user_data = UserDetailSerializer(request.user).data
    
    return Response({
        'user': user_data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token_view(request):
    """Vista para verificar si el token es válido"""
    return Response({
        'valid': True,
        'user_id': request.user.id,
        'username': request.user.username
    }, status=status.HTTP_200_OK)