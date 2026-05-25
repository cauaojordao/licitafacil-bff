from fastapi import APIRouter

from src.app.api.v1.routes.auth import router as auth_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
