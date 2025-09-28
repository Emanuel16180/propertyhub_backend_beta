from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Vehicle(models.Model):
    """Modelo para los vehículos de los residentes"""
    
    VEHICLE_TYPES = (
        ('light', 'Vehículo Ligero'),
        ('heavy', 'Vehículo Pesado'),
        ('motorcycle', 'Motocicleta'),
    )
    
    # Información básica del vehículo
    license_plate = models.CharField('Placa', max_length=20, unique=True, help_text='Ej: ABC123')
    brand = models.CharField('Marca', max_length=50, help_text='Ej: Toyota, Chevrolet')
    model = models.CharField('Modelo', max_length=50, help_text='Ej: Corolla, Spark')
    year = models.PositiveIntegerField('Año', help_text='Ej: 2020')
    color = models.CharField('Color', max_length=30, help_text='Ej: Blanco, Negro, Azul')
    vehicle_type = models.CharField('Tipo de Vehículo', max_length=20, choices=VEHICLE_TYPES)
    
    # Propietario (debe ser residente)
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='vehicles',
        help_text='Residente propietario del vehículo'
    )
    
    # Información de parqueo
    parking_space = models.CharField('Espacio de Parqueo', max_length=50, blank=True, help_text='Ej: P-15, Sótano A-23')
    
    # Observaciones
    observations = models.TextField('Observaciones', blank=True, help_text='Observaciones adicionales del vehículo')
    
    # Estado del vehículo
    is_active = models.BooleanField('Activo', default=True, help_text='Si el vehículo está activo en el sistema')
    
    # Timestamps
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        db_table = 'vehicles'
        ordering = ['license_plate']
    
    def __str__(self):
        return f"{self.license_plate} - {self.brand} {self.model} ({self.owner.get_full_name()})"
    
    @property
    def vehicle_info(self):
        """Información completa del vehículo"""
        return f"{self.brand} {self.model} {self.year} - {self.color}"
    
    @property
    def owner_name(self):
        """Nombre del propietario"""
        return self.owner.get_full_name()
    
    @property
    def owner_house(self):
        """Casa del propietario"""
        if hasattr(self.owner.profile, 'resident_info'):
            return self.owner.profile.resident_info.house_identifier
        return "Sin casa asignada"