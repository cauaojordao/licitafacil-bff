"""Router principal da API v1."""

from fastapi import APIRouter

from src.api.v1.routes.auth import router as auth_router
from src.api.v1.routes.cnpj import router as cnpj_router
from src.api.v1.routes.locations import router as locations_router
from src.api.v1.routes.users import router as users_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(cnpj_router, prefix="/cnpj", tags=["cnpj"])
router.include_router(locations_router, prefix="/locations", tags=["locations"])
