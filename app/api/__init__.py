"""
API Routes Module
---------------
Contiene todas las rutas y endpoints de la API
"""

from fastapi import APIRouter
from app.api.routes import upload

# Crear el router principal
api_router = APIRouter()

# Incluir los routers de las rutas
api_router.include_router(
    upload.router,
    prefix="/upload",
    tags=["upload"]
) 