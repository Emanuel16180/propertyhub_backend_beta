# apps/access_control/models.py

from django.db import models
from django.contrib.auth.models import User # Para relacionar con el residente

class AccessLog(models.Model):
    """Modelo para registrar intentos de acceso (ej. por reconocimiento facial)"""
    
    # Usuario que intenta el acceso. Puede ser nulo si es 'Desconocido'.
    resident = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='access_logs',
        verbose_name="Residente (si reconocido)"
    )
    
    # Identificación del intento
    access_time = models.DateTimeField(auto_now_add=True, verbose_name="Hora de Acceso")
    
    # Detalles del reconocimiento
    confidence = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name="Confianza (%)"
    )
    
    # Resultado del acceso
    is_authorized = models.BooleanField(default=False, verbose_name="Autorizado")
    
    # Mensajes
    main_message = models.CharField(max_length=100, verbose_name="Mensaje Principal")
    detail_message = models.CharField(max_length=255, blank=True, verbose_name="Mensaje de Detalle")
    
    # Tipo de acceso (opcional, para diferenciar cámaras/puntos)
    access_point = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Punto de Acceso (Ej. Puerta Principal)"
    )
    
    class Meta:
        verbose_name = 'Registro de Acceso'
        verbose_name_plural = 'Registros de Acceso'
        db_table = 'access_logs'
        ordering = ['-access_time']
    
    def __str__(self):
        status = "Autorizado" if self.is_authorized else "No Autorizado"
        user = self.resident.get_full_name() if self.resident else "Desconocido"
        return f"{self.access_time.strftime('%Y-%m-%d %H:%M:%S')} - {status} por {user}"