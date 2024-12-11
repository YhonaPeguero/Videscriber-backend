from pathlib import Path
import os
import logging
from pydantic_settings import BaseSettings
from functools import lru_cache

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Configuraciones de la aplicación
    APP_NAME: str = "Video Transcriber API"
    DEBUG: bool = True
    
    # Configuraciones de almacenamiento
    UPLOAD_DIR: Path = Path(__file__).resolve().parent / "api" / "uploads"
    
    class Config:
        env_file = ".env"

# Crear instancia de Settings
settings = Settings()

# Asegurar que el directorio de uploads existe
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Directorio de uploads creado en: {settings.UPLOAD_DIR}")
    
    # Verificar permisos
    if not os.access(settings.UPLOAD_DIR, os.W_OK):
        logger.error(f"No hay permisos de escritura en: {settings.UPLOAD_DIR}")
        raise PermissionError(f"No hay permisos de escritura en: {settings.UPLOAD_DIR}")
        
except Exception as e:
    logger.error(f"Error al configurar directorio de uploads: {e}")
    raise

# Exportar lo necesario
UPLOAD_DIR = settings.UPLOAD_DIR

@lru_cache()
def get_settings():
    return Settings() 