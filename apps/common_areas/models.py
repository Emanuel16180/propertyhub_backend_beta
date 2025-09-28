from django.db import models
from django.utils import timezone
from datetime import time

class CommonArea(models.Model):
    """Modelo para las áreas comunes del condominio"""
    
    AREA_TYPES = (
        ('salon_social', 'Salón Social'),
        ('piscina', 'Piscina'),
        ('gimnasio', 'Gimnasio'),
        ('parque_jardin', 'Parque/Jardín'),
        ('cancha_deportiva', 'Cancha Deportiva'),
        ('zona_bbq', 'Zona BBQ'),
        ('otro', 'Otro'),
    )
    
    # Información básica
    name = models.CharField('Nombre del Área', max_length=100, help_text='Ej: Salón Social, Piscina Principal')
    area_type = models.CharField('Tipo', max_length=20, choices=AREA_TYPES)
    location = models.CharField('Ubicación', max_length=100, help_text='Ej: Primer piso, Torre A')
    capacity = models.PositiveIntegerField('Capacidad (personas)', help_text='Número máximo de personas')
    
    # Horarios de funcionamiento
    start_time = models.TimeField('Hora de Inicio', help_text='Hora de apertura del área')
    end_time = models.TimeField('Hora de Fin', help_text='Hora de cierre del área')
    
    # Configuraciones de reserva
    requires_reservation = models.BooleanField('Requiere reserva previa', default=True)
    
    # Reglas y descripción
    usage_rules = models.TextField('Reglas de Uso', help_text='Reglas y normas para el uso del área común')
    description = models.TextField('Descripción', blank=True, help_text='Descripción adicional del área común')
    
    # Estado del área
    is_active = models.BooleanField('Activa', default=True, help_text='Si el área está disponible para uso')
    is_maintenance = models.BooleanField('En Mantenimiento', default=False, help_text='Si el área está en mantenimiento')
    
    # Timestamps
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Área Común'
        verbose_name_plural = 'Áreas Comunes'
        db_table = 'common_areas'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_area_type_display()})"
    
    @property
    def is_available(self):
        """Verificar si el área está disponible"""
        return self.is_active and not self.is_maintenance
    
    @property
    def operating_hours(self):
        """Horario de funcionamiento formateado"""
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    def is_open_at(self, check_time):
        """Verificar si el área está abierta a una hora específica"""
        if not self.is_available:
            return False
        
        # Manejar horarios que cruzan medianoche
        if self.start_time <= self.end_time:
            return self.start_time <= check_time <= self.end_time
        else:
            # Horario nocturno (ej: 22:00 - 06:00)
            return check_time >= self.start_time or check_time <= self.end_time