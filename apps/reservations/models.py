# apps/reservations/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, timedelta, date

# Importar modelos existentes
from apps.common_areas.models import CommonArea
from apps.properties.models import Property, PropertyResident

class ReservationStatus(models.TextChoices):
    PENDING = 'pending', 'Pendiente'
    CONFIRMED = 'confirmed', 'Confirmada'
    CANCELLED = 'cancelled', 'Cancelada'
    COMPLETED = 'completed', 'Completada'

class Reservation(models.Model):
    """Modelo para reservas de áreas comunes"""
    
    # Relaciones principales
    common_area = models.ForeignKey(
        CommonArea, 
        on_delete=models.CASCADE, 
        related_name='reservations',
        verbose_name="Área Común"
    )
    house_property = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='reservations',
        verbose_name="Propiedad"
    )
    resident = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='resident_reservations',
        verbose_name="Residente"
    )
    
    # Información de la reserva
    date = models.DateField(verbose_name="Fecha de Reserva")
    start_time = models.TimeField(verbose_name="Hora de Inicio")
    end_time = models.TimeField(verbose_name="Hora de Fin")
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    # Estado de la reserva
    status = models.CharField(
        max_length=20, 
        choices=ReservationStatus.choices, 
        default=ReservationStatus.CONFIRMED,
        verbose_name="Estado"
    )
    
    # Auditoría
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_reservations',
        verbose_name="Creado por"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-created_at']
        # Evitar reservas duplicadas para el mismo horario y área
        unique_together = ['common_area', 'date', 'start_time', 'end_time']
    
    def __str__(self):
        return f"{self.common_area.name} - {self.date} ({self.start_time}-{self.end_time})"
    
    def clean(self):
        """Validaciones del modelo"""
        errors = {}
        
        # Validar que la fecha no sea en el pasado
        if self.date and self.date < date.today():
            errors['date'] = 'No se pueden hacer reservas para fechas pasadas.'
        
        # Validar que start_time sea menor que end_time
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors['end_time'] = 'La hora de fin debe ser posterior a la hora de inicio.'
        
        # Validar que el horario esté dentro del horario del área común
        if self.common_area and self.start_time and self.end_time:
            if (self.start_time < self.common_area.start_time or 
                self.end_time > self.common_area.end_time):
                errors['start_time'] = f'El horario debe estar entre {self.common_area.start_time} y {self.common_area.end_time}.'
        
        # Validar que el residente pertenezca a la propiedad seleccionada
        if self.resident and self.house_property:
            # Verificar si el residente es el propietario
            is_owner = self.house_property.owner == self.resident
            
            # O si es residente de la propiedad
            is_resident = PropertyResident.objects.filter(
                property=self.house_property,
                resident=self.resident,
                is_active=True
            ).exists()
            
            if not (is_owner or is_resident):
                errors['resident'] = 'El residente seleccionado no pertenece a la propiedad indicada.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_hours(self):
        """Calcular duración en horas"""
        if self.start_time and self.end_time:
            start_datetime = datetime.combine(date.today(), self.start_time)
            end_datetime = datetime.combine(date.today(), self.end_time)
            duration = end_datetime - start_datetime
            return duration.total_seconds() / 3600
        return 0
    
    @property
    def resident_name(self):
        """Nombre del residente"""
        return self.resident.get_full_name()
    
    @property
    def property_identifier(self):
        """Identificador de la propiedad"""
        return self.house_property.full_identifier
    
    @property
    def can_be_cancelled(self):
        """Verificar si la reserva se puede cancelar"""
        if self.status in ['cancelled', 'completed']:
            return False
        
        # No se puede cancelar si ya pasó la fecha
        if self.date < date.today():
            return False
        
        # No se puede cancelar si es el mismo día y ya pasó la hora
        if self.date == date.today():
            now = timezone.now().time()
            if now >= self.start_time:
                return False
        
        return True
    
    @classmethod
    def get_available_time_slots(cls, common_area, reservation_date):
        """Obtener horarios disponibles para una fecha y área específica"""
        if reservation_date < date.today():
            return []
        
        # Crear lista de horarios de 1 hora
        slots = []
        current_time = datetime.combine(reservation_date, common_area.start_time)
        end_time = datetime.combine(reservation_date, common_area.end_time)
        
        while current_time < end_time:
            slot_end = current_time + timedelta(hours=1)
            if slot_end.time() <= common_area.end_time:
                # Verificar si este horario está ocupado
                is_occupied = cls.objects.filter(
                    common_area=common_area,
                    date=reservation_date,
                    status='confirmed',
                    start_time__lt=slot_end.time(),
                    end_time__gt=current_time.time()
                ).exists()
                
                # Si es hoy, verificar que no haya pasado la hora
                is_past = False
                if reservation_date == date.today():
                    now = timezone.now().time()
                    if current_time.time() <= now:
                        is_past = True
                
                slots.append({
                    'start_time': current_time.time().strftime('%H:%M'),
                    'end_time': slot_end.time().strftime('%H:%M'),
                    'display': f"{current_time.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}",
                    'available': not (is_occupied or is_past),
                    'is_past': is_past,
                    'is_occupied': is_occupied
                })
            
            current_time += timedelta(hours=1)
        
        return slots