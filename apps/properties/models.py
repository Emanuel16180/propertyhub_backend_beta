from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Property(models.Model):
    """Modelo para las casas/propiedades del condominio"""
    
    STATUS_CHOICES = (
        ('available', 'Disponible'),
        ('occupied', 'Ocupada'),
        ('maintenance', 'En Mantenimiento'),
        ('reserved', 'Reservada'),
    )
    
    # Información básica de identificación
    house_number = models.CharField('Número de Casa', max_length=50, unique=True, help_text='Ej: 101, A-205')
    block = models.CharField('Bloque', max_length=50, help_text='Ej: A, B, Torre 1')
    floor = models.CharField('Piso', max_length=10, blank=True, help_text='Ej: 1, 2, 3')
    
    # Propietario (puede estar vacío al crear la casa)
    owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='owned_properties',
        help_text='Propietario actual de la propiedad'
    )
    
    # Características físicas
    area_m2 = models.DecimalField('Área (m²)', max_digits=8, decimal_places=2)
    bedrooms = models.PositiveIntegerField('Habitaciones', default=1)
    bathrooms = models.PositiveIntegerField('Baños', default=1)
    parking_spaces = models.PositiveIntegerField('Espacios de Parqueo', default=0)
    
    # Estado y descripción
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='available')
    description = models.TextField('Descripción', blank=True, help_text='Descripción adicional de la propiedad')
    
    # Timestamps
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Propiedad'
        verbose_name_plural = 'Propiedades'
        db_table = 'properties'
        ordering = ['block', 'house_number']
    
    def __str__(self):
        return f"{self.house_number} - Bloque {self.block}"
    
    @property
    def full_identifier(self):
        """Identificador completo de la propiedad"""
        if self.floor:
            return f"{self.house_number} - Bloque {self.block}, Piso {self.floor}"
        return f"{self.house_number} - Bloque {self.block}"
    
    @property
    def owner_name(self):
        """Nombre del propietario si existe"""
        if self.owner:
            return self.owner.get_full_name()
        return "Sin propietario asignado"
    
    @property
    def is_available(self):
        """Verificar si la propiedad está disponible"""
        return self.status == 'available'


class PropertyResident(models.Model):
    """Modelo para vincular residentes adicionales a una propiedad"""
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='residents')
    resident = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resided_properties')
    
    # Relación del residente con la propiedad
    relationship = models.CharField('Relación', max_length=50, help_text='Ej: Familiar, Inquilino, etc.')
    is_primary_resident = models.BooleanField('Residente Principal', default=False)
    
    # Fechas
    move_in_date = models.DateField('Fecha de Ingreso', default=timezone.now)
    move_out_date = models.DateField('Fecha de Salida', null=True, blank=True)
    is_active = models.BooleanField('Activo', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Residente de Propiedad'
        verbose_name_plural = 'Residentes de Propiedades'
        db_table = 'property_residents'
        unique_together = ['property', 'resident']
    
    def __str__(self):
        return f"{self.resident.get_full_name()} - {self.property.full_identifier}"