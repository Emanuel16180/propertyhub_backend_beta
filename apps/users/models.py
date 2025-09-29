from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from .storage import SupabaseStorage

class UserProfile(models.Model):
    """Perfil extendido para todos los usuarios"""
    
    USER_TYPES = (
        ('admin', 'Administrador'),
        ('security', 'Seguridad'),
        ('camera', 'Cámara'),
        ('resident', 'Residente'),
    )
    
    # Relación con el User de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Tipo de usuario
    user_type = models.CharField('Tipo de usuario', max_length=20, choices=USER_TYPES)
    
    # Información básica adicional
    phone = models.CharField('Teléfono', max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_user_type_display()})"


class ResidentProfile(models.Model):
    """Perfil adicional solo para residentes"""
    
    RESIDENT_TYPES = (
        ('owner', 'Propietario'),
        ('family', 'Familiar'),
        ('tenant', 'Inquilino'),
    )
    
    # Relación con UserProfile
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='resident_info')
    
    # Información específica de residentes
    resident_type = models.CharField('Tipo de residente', max_length=20, choices=RESIDENT_TYPES)
    birth_date = models.DateField('Fecha de nacimiento')
    #face_photo = models.ImageField('Foto del rostro', upload_to='resident_photos/', blank=True, null=True)
    face_photo = models.ImageField(
        'Foto del rostro',
        storage=SupabaseStorage(),   # 👈 fuerza a usar Supabase
        blank=True,
        null=True
    )
    
    # Vinculación con casa (por ahora dejamos solo el campo, sin FK)
    house_identifier = models.CharField('Identificador de casa', max_length=50, blank=True, help_text='Por ahora solo texto, después será FK')
    
    # Timestamps
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Residente'
        verbose_name_plural = 'Perfiles de Residentes'
        db_table = 'resident_profiles'
    
    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} - {self.get_resident_type_display()}"
    
    @property
    def age(self):
        """Calcula la edad del residente"""
        today = timezone.now().date()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))