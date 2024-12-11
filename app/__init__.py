# Archivo __init__.py principal de la aplicación

"""
Video Transcriber Backend API
----------------------------
API para transcripción de videos usando Whisper
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, logger
from app.api import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="API para transcripción de videos",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir router principal
app.include_router(api_router, prefix="/api")
