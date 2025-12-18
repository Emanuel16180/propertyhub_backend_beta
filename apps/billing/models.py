from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from apps.properties.models import Property
from django.core.exceptions import ValidationError

class PaymentCategory(models.Model):
    """Categorías de ingresos y egresos"""
    
    TYPE_CHOICES = (
        ('income', 'Ingreso'),
        ('expense', 'Egreso'),
    )
    
    name = models.CharField('Nombre', max_length=100)
    type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES)
    description = models.TextField('Descripción', blank=True)
    is_active = models.BooleanField('Activo', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Categoría de Pago'
        verbose_name_plural = 'Categorías de Pago'
        db_table = 'payment_categories'
        ordering = ['type', 'name']
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"


class Transaction(models.Model):
    """Modelo principal para movimientos financieros (Cobros y Pagos)"""
    
    TRANSACTION_TYPE_CHOICES = (
        ('income', 'Cobro (Ingreso)'),
        ('expense', 'Pago (Egreso)'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('cancelled', 'Anulado'),
    )
    
    # Información básica
    transaction_type = models.CharField('Tipo de Movimiento', max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    category = models.ForeignKey(PaymentCategory, on_delete=models.PROTECT, related_name='transactions', verbose_name='Categoría')
    
    # Relación con propiedad (Obligatorio para Cobros, Opcional para Pagos generales)
    property = models.ForeignKey(
        Property, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='transactions',
        verbose_name='Propiedad/Unidad'
    )
    
    # Detalle financiero
    amount = models.DecimalField('Monto', max_digits=10, decimal_places=2)
    concept = models.CharField('Concepto', max_length=150, help_text='Título breve del movimiento')
    description = models.TextField('Descripción', blank=True)
    
    # Estado y Flujo
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Fechas
    issue_date = models.DateField('Fecha de Emisión/Registro', default=timezone.localdate)
    due_date = models.DateField('Fecha de Vencimiento', null=True, blank=True, help_text='Solo para cobros')
    payment_date = models.DateField('Fecha de Pago Real', null=True, blank=True)
    
    # Auditoría
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_transactions',
        verbose_name='Registrado por'
    )
    
    # Timestamps internos
    created_at = models.DateTimeField('Creado (Timestamp)', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado (Timestamp)', auto_now=True)
    
    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        db_table = 'transactions'
        ordering = ['-issue_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['issue_date']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.concept} ({self.amount})"
    
    def clean(self):
        # Validaciones de Integridad
        
        # 1. Validar que el monto sea positivo
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({'amount': 'El monto debe ser mayor a 0.'})
            
        # 2. Validar consistencia de Categoría
        if self.category_id:
            if self.transaction_type == 'income' and self.category.type != 'income':
                raise ValidationError({'category': 'La categoría seleccionada no corresponde a un Ingreso.'})
            if self.transaction_type == 'expense' and self.category.type != 'expense':
                raise ValidationError({'category': 'La categoría seleccionada no corresponde a un Egreso.'})
                
        # 3. Validar Propiedad para Cobros (Ingresos)
        if self.transaction_type == 'income' and not self.property:
             # Nota: A veces puede haber ingresos generales no ligados a casas, pero el requerimiento dice "Casa/Unidad: Relación... (solo obligatoria para Cobros)"
             # Seremos estrictos según requerimiento, o flexibles si se asume ingresos varios.
             # Asumiremos estricto por ahora según "Casa/Unidad: Relación con la tabla de propiedades (solo obligatoria para Cobros)"
             raise ValidationError({'property': 'Para registrar un Cobro es obligatorio seleccionar una Propiedad.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
