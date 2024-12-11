from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
import os
import whisper
from pydantic import BaseModel
import logging
from moviepy.editor import VideoFileClip
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener la ruta base del proyecto (un nivel arriba de la carpeta app)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

router = APIRouter()

# Modelo para la respuesta de transcripción
class TranscriptionResponse(BaseModel):
    status: str
    text: str = None
    error: str = None
    progress: float = 0.0

# Almacén en memoria para el estado de las transcripciones
transcription_status: Dict[str, Dict] = {}

# Pool de hilos para procesamiento asíncrono
thread_pool = ThreadPoolExecutor(max_workers=3)

def check_video_file(file_path: str) -> bool:
    """Verifica si el archivo es un video válido"""
    try:
        with VideoFileClip(file_path) as clip:
            duration = clip.duration
            logger.info(f"Video válido encontrado. Duración: {duration} segundos")
            return True
    except Exception as e:
        logger.error(f"Error al verificar el video: {str(e)}")
        return False

async def process_transcription(filename: str, file_path: str):
    """Procesa la transcripción en segundo plano"""
    try:
        # Actualizar estado inicial
        transcription_status[filename] = {
            "status": "processing",
            "text": None,
            "progress": 0.0
        }

        # Verificar el archivo de video
        if not check_video_file(file_path):
            transcription_status[filename] = {
                "status": "error",
                "error": "El archivo de video no es válido o está corrupto",
                "progress": 0
            }
            return

        # Cargar el modelo de Whisper
        logger.info("Cargando modelo Whisper...")
        model = whisper.load_model("base")
        transcription_status[filename]["progress"] = 30.0

        # Realizar la transcripción en un hilo separado
        logger.info("Iniciando transcripción...")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            thread_pool,
            lambda: model.transcribe(file_path)
        )

        # Guardar el resultado
        transcription_status[filename] = {
            "status": "completed",
            "text": result["text"],
            "progress": 100.0
        }
        logger.info(f"Transcripción completada para {filename}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error en la transcripción: {error_msg}")
        transcription_status[filename] = {
            "status": "error",
            "error": error_msg,
            "progress": 0.0
        }

@router.get("/{filename}")
async def get_transcription_status(filename: str):
    try:
        # Limpiar el nombre del archivo
        safe_filename = filename.replace("\\", "").replace("/", "")
        
        # Usar Path para manejar la ruta correctamente
        file_path = Path(UPLOAD_DIR) / safe_filename
        logger.info(f"Buscando archivo en: {file_path}")
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Archivo no encontrado: {safe_filename}"
            )
            
        # Verificar si el archivo existe
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado: {file_path}")
            return {
                "status": "error",
                "error": f"Archivo no encontrado en {file_path}",
                "progress": 0
            }
        
        # Verificar si ya existe una transcripción
        if filename in transcription_status:
            logger.info(f"Estado de transcripción encontrado para {filename}")
            return transcription_status[filename]
        
        # Si no existe, iniciar la transcripción en segundo plano
        logger.info(f"Iniciando nueva transcripción para {filename}")
        background_tasks.add_task(process_transcription, filename, file_path)
        
        # Devolver estado inicial
        return {
            "status": "processing",
            "text": None,
            "progress": 0.0
        }
        
    except Exception as e:
        logger.error(f"Error en transcripción: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/transcription/{filename}")
async def delete_transcription(filename: str):
    logger.info(f"Eliminando transcripción para {filename}")
    if filename in transcription_status:
        del transcription_status[filename]
    return {"status": "success", "message": "Transcripción eliminada"}
