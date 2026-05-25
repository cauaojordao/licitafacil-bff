"""Ponto de entrada principal da aplicação FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import router as v1_router
from src.core.config import settings
from src.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra routers da API
app.include_router(v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """
    Endpoint de health check.

    Returns:
        Status da aplicação
    """
    return {"status": "ok"}
