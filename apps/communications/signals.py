import firebase_admin
from firebase_admin import credentials, messaging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Communication # Importa tu modelo de Avisos

# 1. Inicializar Firebase Admin (Hazlo una sola vez, quizás en settings.py es mejor, pero aquí sirve para probar)
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json") # Ruta a tu JSON
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Error init firebase: {e}")

@receiver(post_save, sender=Communication)
def send_notification_on_new_notice(sender, instance, created, **kwargs):
    if created: # Solo si es un aviso NUEVO
        try:
            # 2. Construir el mensaje
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"Nuevo Aviso: {instance.title}", # Asumiendo que tu modelo tiene 'title'
                    body=instance.message[:100], # Primeros 100 caracteres del mensaje
                ),
                topic='avisos', # Enviamos al tema al que se suscribió Flutter
                data={
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                    'view': 'avisos', # Para que Flutter sepa a dónde navegar
                    'id': str(instance.id)
                }
            )

            # 3. Enviar
            response = messaging.send(message)
            print('✅ Notificación enviada exitosamente:', response)
            
        except Exception as e:
            print('❌ Error enviando notificación:', e)