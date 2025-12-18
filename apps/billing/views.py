from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import PaymentCategory, Transaction
from .serializers import (
    PaymentCategorySerializer, 
    TransactionSerializer, 
    BatchTransactionSerializer,
    DashboardStatsSerializer
)
from apps.properties.models import Property
from django.utils import timezone

class PaymentCategoryViewSet(viewsets.ModelViewSet):
    queryset = PaymentCategory.objects.all()
    serializer_class = PaymentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    filterset_fields = ['type', 'is_active']

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated] # Asumimos IsAdminOrTreasurer si existiera, por ahora Auth genérico
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['concept', 'description', 'property__house_number']
    filterset_fields = ['transaction_type', 'category', 'property', 'status', 'issue_date']
    ordering_fields = ['issue_date', 'created_at', 'amount']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'], url_path='batch-create')
    def batch_create(self, request):
        """
        Registro masivo de cobros para todas las propiedades activas.
        """
        serializer = BatchTransactionSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.validated_data['category']
            amount = serializer.validated_data['amount']
            concept = serializer.validated_data['concept']
            description = serializer.validated_data.get('description', '')
            due_date = serializer.validated_data.get('due_date')
            
            # Obtener todas las propiedades (podríamos filtrar por status='occupied' si fuera requerido, 
            # pero el requerimiento dice "todas las casas activas")
            # Asumiremos status__in=['occupied', 'available', 'reserved'] o simplemente todas las que existen.
            # "casas activas" podría interpretarse como no eliminadas o en un estado válido. 
            # Usaremos todas las del modelo Property por defecto.
            properties = Property.objects.all()
            
            transactions_to_create = []
            
            with transaction.atomic():
                for prop in properties:
                    transactions_to_create.append(Transaction(
                        transaction_type='income', # Batch es típicamente para cobros (expensas)
                        category=category,
                        property=prop,
                        amount=amount,
                        concept=concept,
                        description=description,
                        status='pending',
                        issue_date=timezone.now().date(),
                        due_date=due_date,
                        created_by=request.user
                    ))
                
                created_transactions = Transaction.objects.bulk_create(transactions_to_create)
                
            return Response(
                {"message": f"Se generaron {len(created_transactions)} cobros correctamente."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Estadísticas para los cards del dashboard:
        - Total Cobros (Ingresos)
        - Total Pagos (Egresos)
        - Balance
        - Cobros Pendientes
        """
        # Filtrar por query params si se desea estadísticas de un rango/filtro específico
        # pero típicamente es global o mes actual. 
        # Implementaremos global basado en filtros actuales del queryset si se aplicaran, 
        # pero para dashboard suele ser "todo" o "mes actual". 
        # El requerimiento no especifica rango, asumimos GLOBAL histórico o lo que venga en filtros.
        # Para simplificar y ser útil, usaremos el queryset filtrado (respetando filtros de UI).
        
        queryset = self.filter_queryset(self.get_queryset())
        
        # Agregaciones
        aggregates = queryset.aggregate(
            total_income=Sum('amount', filter=Q(transaction_type='income')),
            total_expense=Sum('amount', filter=Q(transaction_type='expense')),
            pending_incomes_count=Count('id', filter=Q(transaction_type='income', status='pending'))
        )
        
        total_income = aggregates['total_income'] or 0
        total_expense = aggregates['total_expense'] or 0
        balance = total_income - total_expense
        pending_incomes_count = aggregates['pending_incomes_count'] or 0
        
        data = {
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance,
            'pending_incomes_count': pending_incomes_count
        }
        
        return Response(data)
