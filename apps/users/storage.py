from django.core.files.storage import Storage
from django.conf import settings
from supabase import create_client
import uuid
from io import BytesIO

class SupabaseStorage(Storage):
    def __init__(self):
        self.client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.bucket = 'resident-photos'
    
    def _save(self, name, content):
        # Generar nombre único
        ext = name.split('.')[-1] if '.' in name else 'jpg'
        filename = f"face_{uuid.uuid4().hex[:16]}.{ext}"
        
        # Leer contenido
        content.seek(0)
        file_bytes = content.read()
        
        # Subir a Supabase
        self.client.storage.from_(self.bucket).upload(
            filename,
            file_bytes,
            {'content-type': getattr(content, 'content_type', 'image/jpeg')}
        )
        
        return filename
    
    def url(self, name):
        if not name:
            return ''
        # URL pública del bucket
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket}/{name}"
    
    def exists(self, name):
        try:
            files = self.client.storage.from_(self.bucket).list()
            return any(f['name'] == name for f in files)
        except:
            return False
    
    def delete(self, name):
        try:
            self.client.storage.from_(self.bucket).remove([name])
        except:
            pass
    
    def size(self, name):
        return 0  # No implementado