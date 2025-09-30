# apps/security/models.py

from django.db import models
from django.contrib.auth.models import User

class IntrusionLog(models.Model):
    """Modelo para registrar detecciones de intrusos o eventos de vigilancia."""

    # Evento
    message = models.CharField(
        'Mensaje de Alerta', 
        max_length=255, 
        help_text='Ej: Intruso detectado, Persona no reconocida.'
    )
    confidence = models.DecimalField(
        'Confianza (%)', 
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text='Nivel de confianza de la detección si aplica.'
    )
    
    # Ubicación y Tiempo
    detection_time = models.DateTimeField('Hora de Detección', auto_now_add=True)
    camera_identifier = models.CharField(
        'Cámara/Punto de Detección', 
        max_length=50, 
        blank=True, 
        help_text='Ej: Camara 1, Acceso Principal'
    )
    
    # Estado (para seguimiento)
    is_resolved = models.BooleanField('Resuelto', default=False)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='resolved_intrusions',
        verbose_name='Resuelto por'
    )
    
    class Meta:
        verbose_name = 'Registro de Intrusión'
        verbose_name_plural = 'Registros de Intrusos'
        ordering = ['-detection_time']
        db_table = 'intrusion_logs'
    
    def __str__(self):
        return f"ALARMA: {self.message} en {self.camera_identifier} ({self.detection_time.strftime('%Y-%m-%d %H:%M')})"