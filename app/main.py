from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, UPLOAD_DIR
import os
from pathlib import Path

app = FastAPI(
    title=settings.APP_NAME,
    description="API para transcripción de videos",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "API running"}

@app.get("/api/upload/test")
async def test_upload():
    return {"message": "Upload endpoint funcionando"}

@app.get("/api/upload/check")
async def check_upload_dir():
    try:
        exists = UPLOAD_DIR.exists()
        return {
            "exists": exists,
            "is_dir": UPLOAD_DIR.is_dir() if exists else False,
            "writable": os.access(UPLOAD_DIR, os.W_OK) if exists else False,
            "path": str(UPLOAD_DIR),
            "contents": [f.name for f in UPLOAD_DIR.iterdir()] if exists else []
        }
    except Exception as e:
        # Manejar cualquier error que pueda ocurrir al verificar el directorio
        return {
            "error": str(e),
            "status": "error",
            "upload_dir": str(UPLOAD_DIR)
        }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Sube un archivo al servidor"""
    try:
        # Log información del archivo
        logger.info(f"Recibiendo archivo: {file.filename}")
        
        # Validar extensión del archivo
        file_ext = file.filename.lower().split('.')[-1]
        if f".{file_ext}" not in settings.SUPPORTED_FORMATS:
            supported_formats_str = ", ".join(settings.SUPPORTED_FORMATS)
            raise HTTPException(
                status_code=400,
                detail=f"Formato de archivo no soportado. Formatos permitidos: {supported_formats_str}"
            )
        
        # Validar tamaño del archivo
        content = await file.read()
        if len(content) > settings.MAX_CONTENT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo demasiado grande. Tamaño máximo permitido: {settings.MAX_CONTENT_LENGTH / (1024*1024)}MB"
            )
        
        # Crear ruta completa del archivo
        file_path = UPLOAD_DIR / file.filename
        logger.info(f"Guardando archivo en: {file_path}")
        
        try:
            # Guardar el archivo
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Verificar que el archivo existe y su tamaño
            if file_path.exists():
                file_size = file_path.stat().st_size
                logger.info(f"Archivo guardado exitosamente - Tamaño: {file_size} bytes")
                
                return {
                    "filename": file.filename,
                    "size": file_size,
                    "format": file_ext,
                    "status": "success",
                    "message": "Archivo subido exitosamente"
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="El archivo no se guardó correctamente"
                )
                
        except Exception as e:
            logger.error(f"Error al guardar el archivo: {str(e)}")
            if file_path.exists():
                file_path.unlink()  # Eliminar el archivo si hubo error
            raise HTTPException(
                status_code=500,
                detail=f"Error al guardar el archivo: {str(e)}"
            )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error en el proceso de upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Incluir todas las rutas de la API
app.include_router(api_router, prefix="/api")

# Evento de inicio
@app.on_event("startup")
async def startup_event():
    """Evento que se ejecuta al iniciar la aplicación"""
    logger.info("Iniciando servidor FastAPI...")
    # Asegurar que el directorio de uploads existe
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Servidor iniciado correctamente")
