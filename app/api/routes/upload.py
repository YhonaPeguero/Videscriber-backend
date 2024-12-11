from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import settings, logger
import os
from pathlib import Path

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Endpoint de prueba simple"""
    return {"message": "Upload endpoint funcionando"}

@router.get("/check")
async def check_upload_dir():
    """Verificar el estado del directorio de uploads"""
    try:
        upload_dir = settings.UPLOAD_DIR
        exists = upload_dir.exists()
        
        return {
            "exists": exists,
            "is_dir": upload_dir.is_dir() if exists else False,
            "writable": os.access(upload_dir, os.W_OK) if exists else False,
            "path": str(upload_dir),
            "contents": [f.name for f in upload_dir.iterdir()] if exists else []
        }
    except Exception as e:
        logger.error(f"Error al verificar directorio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """Subir un archivo"""
    try:
        logger.info(f"Iniciando subida de archivo: {file.filename}")
        logger.info(f"Directorio de uploads: {settings.UPLOAD_DIR}")
        
        # Limpiar el nombre del archivo
        safe_filename = file.filename.replace("\\", "").replace("/", "")
        logger.info(f"Nombre de archivo limpio: {safe_filename}")
        
        # Asegurar que el directorio existe
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Usar Path para manejar la ruta correctamente
        file_path = Path(settings.UPLOAD_DIR) / safe_filename
        logger.info(f"Guardando archivo en: {file_path}")
        
        # Guardar el archivo
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Verificar que el archivo se guardó correctamente
        if file_path.exists():
            logger.info(f"Archivo guardado exitosamente en: {file_path}")
            logger.info(f"Tamaño del archivo: {file_path.stat().st_size} bytes")
        
        return {
            "filename": safe_filename,
            "status": "success",
            "message": "Archivo subido exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error al subir archivo: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 