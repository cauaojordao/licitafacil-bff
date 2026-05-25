"""Router principal da API v1."""

from fastapi import APIRouter

from src.api.v1.routes.auth import router as auth_router

router = APIRouter()

# Registra rotas de autenticação
router.include_router(auth_router, prefix="/auth", tags=["auth"])
