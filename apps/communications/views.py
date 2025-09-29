# apps/communications/views.py
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Communication, CommunicationRead
from .serializers import (
    CommunicationSerializer, 
    CreateCommunicationSerializer,
    CommunicationReadSerializer
)

class CommunicationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

class CommunicationListCreateView(generics.ListCreateAPIView):
    """
    GET: Lista todos los comunicados activos
    POST: Crea un nuevo comunicado
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CommunicationPagination
    
    def get_queryset(self):
        queryset = Communication.objects.filter(is_active=True)
        
        # Filtrar por tipo de comunicado
        comm_type = self.request.query_params.get('type', None)
        if comm_type:
            queryset = queryset.filter(communication_type=comm_type)
        
        # Filtrar por prioridad
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filtrar por audiencia objetivo
        audience = self.request.query_params.get('audience', None)
        if audience:
            queryset = queryset.filter(target_audience=audience)
        
        # Buscar por título o contenido
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(message__icontains=search)
            )
        
        # Solo comunicados no expirados
        now = timezone.now()
        queryset = queryset.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )
        
        return queryset.select_related('author').prefetch_related('read_by')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateCommunicationSerializer
        return CommunicationSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class CommunicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Obtiene un comunicado específico
    PUT/PATCH: Actualiza un comunicado (solo el autor)
    DELETE: Elimina un comunicado (solo el autor)
    """
    queryset = Communication.objects.all()
    serializer_class = CommunicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        obj = super().get_object()
        
        # Marcar como leído automáticamente al obtener el detalle
        CommunicationRead.objects.get_or_create(
            communication=obj,
            user=self.request.user
        )
        
        return obj
    
    def update(self, request, *args, **kwargs):
        communication = self.get_object()
        
        # Solo el autor puede modificar
        if communication.author != request.user:
            return Response(
                {'error': 'Solo el autor puede modificar este comunicado.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        communication = self.get_object()
        
        # Solo el autor puede eliminar
        if communication.author != request.user:
            return Response(
                {'error': 'Solo el autor puede eliminar este comunicado.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete - marcar como inactivo
        communication.is_active = False
        communication.save()
        
        return Response(
            {'message': 'Comunicado eliminado correctamente.'},
            status=status.HTTP_200_OK
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_as_read(request, communication_id):
    """
    Marcar un comunicado como leído
    """
    communication = get_object_or_404(Communication, id=communication_id)
    
    read_record, created = CommunicationRead.objects.get_or_create(
        communication=communication,
        user=request.user
    )
    
    if created:
        return Response(
            {'message': 'Comunicado marcado como leído.'},
            status=status.HTTP_201_CREATED
        )
    else:
        return Response(
            {'message': 'El comunicado ya estaba marcado como leído.'},
            status=status.HTTP_200_OK
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_communications(request):
    """
    Obtener comunicados creados por el usuario actual
    """
    communications = Communication.objects.filter(
        author=request.user
    ).annotate(
        read_count=Count('read_by')
    )
    
    serializer = CommunicationSerializer(
        communications, 
        many=True, 
        context={'request': request}
    )
    
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def communication_stats(request):
    """
    Estadísticas de comunicados
    """
    total_communications = Communication.objects.filter(is_active=True).count()
    
    # Comunicados por tipo
    by_type = Communication.objects.filter(is_active=True).values(
        'communication_type'
    ).annotate(count=Count('id'))
    
    # Comunicados por prioridad
    by_priority = Communication.objects.filter(is_active=True).values(
        'priority'
    ).annotate(count=Count('id'))
    
    # Comunicados del usuario actual
    user_communications = Communication.objects.filter(
        author=request.user,
        is_active=True
    ).count()
    
    # Comunicados no leídos por el usuario
    unread_count = Communication.objects.filter(
        is_active=True
    ).exclude(
        read_by__user=request.user
    ).count()
    
    return Response({
        'total_communications': total_communications,
        'by_type': list(by_type),
        'by_priority': list(by_priority),
        'user_communications': user_communications,
        'unread_count': unread_count
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def urgent_communications(request):
    """
    Obtener solo comunicados urgentes
    """
    urgent_comms = Communication.objects.filter(
        communication_type='urgent',
        is_active=True
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    )
    
    serializer = CommunicationSerializer(
        urgent_comms, 
        many=True, 
        context={'request': request}
    )
    
    return Response(serializer.data)