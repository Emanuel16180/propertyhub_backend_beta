# apps/communications/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CommunicationType(models.TextChoices):
    URGENT = 'urgent', 'Urgente'
    GENERAL = 'general', 'Anuncio General'
    MAINTENANCE = 'maintenance', 'Mantenimiento'
    EVENT = 'event', 'Evento'

class Priority(models.TextChoices):
    LOW = 'baja', 'Baja'
    MEDIUM = 'media', 'Media'
    HIGH = 'alta', 'Alta'

class TargetAudience(models.TextChoices):
    ALL_RESIDENTS = 'all_residents', 'Todos los Residentes'
    OWNERS_ONLY = 'owners_only', 'Solo Propietarios'
    TENANTS_ONLY = 'tenants_only', 'Solo Inquilinos'

class Communication(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título del Comunicado")
    message = models.TextField(verbose_name="Mensaje")
    communication_type = models.CharField(
        max_length=20, 
        choices=CommunicationType.choices, 
        default=CommunicationType.GENERAL,
        verbose_name="Tipo de Comunicado"
    )
    priority = models.CharField(
        max_length=10, 
        choices=Priority.choices, 
        default=Priority.MEDIUM,
        verbose_name="Prioridad"
    )
    target_audience = models.CharField(
        max_length=20,
        choices=TargetAudience.choices,
        default=TargetAudience.ALL_RESIDENTS,
        verbose_name="Dirigido a"
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='communications',
        verbose_name="Autor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Campos adicionales para funcionalidad avanzada
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    attachments = models.FileField(
        upload_to='communications/attachments/', 
        blank=True, 
        null=True
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Comunicado"
        verbose_name_plural = "Comunicados"
    
    def __str__(self):
        return f"{self.get_communication_type_display()}: {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.published_at and self.is_active:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

class CommunicationRead(models.Model):
    """Modelo para trackear quién ha leído cada comunicado"""
    communication = models.ForeignKey(
        Communication, 
        on_delete=models.CASCADE, 
        related_name='read_by'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('communication', 'user')
        verbose_name = "Lectura de Comunicado"
        verbose_name_plural = "Lecturas de Comunicados"
    
    def __str__(self):
        return f"{self.user.username} leyó: {self.communication.title}"