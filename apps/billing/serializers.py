from rest_framework import serializers
from .models import PaymentCategory, Transaction
from apps.properties.models import Property

class PaymentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentCategory
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    property_identifier = serializers.CharField(source='property.full_identifier', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'category', 'category_name',
            'property', 'property_identifier', 'amount', 'concept',
            'description', 'status', 'issue_date', 'due_date',
            'payment_date', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Validaciones personalizadas a nivel de serializer para integridad
        """
        # Delegar validaciones complejas al modelo si es necesario,
        # pero DRF valida campos requeridos automáticamente basándose en el modelo.
        # Aquí podemos agregar mensajes amigables si falla la validación del modelo.
        instance = Transaction(**data)
        try:
            instance.clean()
        except Exception as e:
            # clean() lanza ValidationError de Django, lo convertimos a DRF ValidationError
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
        return data


class BatchTransactionSerializer(serializers.Serializer):
    """
    Serializer para la creación masiva de cobros (Aplicar a todas las casas)
    """
    category = serializers.PrimaryKeyRelatedField(queryset=PaymentCategory.objects.filter(type='income'))
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    concept = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, allow_blank=True)
    due_date = serializers.DateField(required=False, allow_null=True)


class DashboardStatsSerializer(serializers.Serializer):
    """
    Serializer para devolver estadísticas (no guarda datos)
    """
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_incomes_count = serializers.IntegerField()
