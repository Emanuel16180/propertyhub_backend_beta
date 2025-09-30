# apps/visitor_control/models.py

from django.db import models
from django.contrib.auth.models import User
from apps.properties.models import Property # Para la casa a visitar
from apps.common_areas.models import CommonArea # Para el área común a visitar

# --- CHOICES ---
class VisitReason(models.TextChoices):
    FAMILY = 'visita_familiar', 'Visita Familiar'
    DELIVERY = 'delivery', 'Delivery'
    WORK_SERVICE = 'trabajo_servicio', 'Trabajo/Servicio'
    TECHNICAL_SERVICE = 'servicio_tecnico', 'Servicio Técnico'
    OTHER = 'otro', 'Otro'

class VehicleType(models.TextChoices):
    LIGHT = 'light', 'Vehículo Liviano'
    HEAVY = 'heavy', 'Vehículo Pesado'
    MOTORCYCLE = 'motorcycle', 'Motocicleta'

# --- MAIN MODELS ---
class VisitorLog(models.Model):
    """Modelo para el registro de entrada de visitantes"""

    # Datos Personales del Visitante
    full_name = models.CharField('Nombre Completo', max_length=150)
    document_id = models.CharField('Cédula/CI', max_length=50, blank=True)
    document_photo_front = models.FileField(
        'Foto Anverso CI', 
        upload_to='visitors/documents/', 
        blank=True, 
        null=True
    )
    document_photo_back = models.FileField(
        'Foto Reverso CI', 
        upload_to='visitors/documents/', 
        blank=True, 
        null=True
    )

    # Información de Visita
    reason = models.CharField(
        'Motivo de Visita', 
        max_length=50, 
        choices=VisitReason.choices,
        default=VisitReason.FAMILY
    )
    
    # Destino (FK a Propiedad o Área Común) - Ambos pueden ser NULL si es un servicio general
    property_to_visit = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='property_visitors',
        verbose_name='Casa/Propiedad a Visitar'
    )
    common_area_to_visit = models.ForeignKey(
        CommonArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='area_visitors',
        verbose_name='Área Común a Visitar'
    )
    
    # Observaciones y Auditoría
    observations = models.TextField('Observaciones', blank=True)
    check_in_time = models.DateTimeField('Hora de Ingreso', auto_now_add=True)
    check_out_time = models.DateTimeField('Hora de Salida', null=True, blank=True)
    is_active = models.BooleanField('Activo', default=True, help_text='Indica si el visitante sigue dentro del condominio')
    registered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_visitors',
        verbose_name='Registrado por'
    )

    class Meta:
        verbose_name = 'Registro de Visitante'
        verbose_name_plural = 'Registros de Visitantes'
        ordering = ['-check_in_time']
        db_table = 'visitor_logs'
    
    def __str__(self):
        return f"Visita: {self.full_name} a {self.get_destination_display()}"
    
    def get_destination_display(self):
        if self.property_to_visit:
            return self.property_to_visit.full_identifier
        elif self.common_area_to_visit:
            return self.common_area_to_visit.name
        return "Sin Destino Específico"


class VisitVehicle(models.Model):
    """Modelo para el vehículo asociado a una visita"""
    
    visitor_log = models.OneToOneField(
        VisitorLog, 
        on_delete=models.CASCADE, 
        related_name='vehicle',
        verbose_name="Visita Asociada"
    )
    license_plate = models.CharField('Placa', max_length=20)
    color = models.CharField('Color', max_length=30, blank=True)
    model = models.CharField('Modelo', max_length=50, blank=True)
    vehicle_type = models.CharField(
        'Tipo de Vehículo', 
        max_length=20, 
        choices=VehicleType.choices,
        default=VehicleType.LIGHT
    )
    
    class Meta:
        verbose_name = 'Vehículo de Visita'
        verbose_name_plural = 'Vehículos de Visita'
        db_table = 'visit_vehicles'
        
    def __str__(self):
        return f"{self.license_plate} ({self.visitor_log.full_name})"