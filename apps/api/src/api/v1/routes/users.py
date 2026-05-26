"""Rotas para gerenciamento de usuários."""

from fastapi import APIRouter, Depends, Query, status

from src.core.dependencies import get_token_service, get_user_mei_service
from src.domain.schemas.auth import TokenResponse
from src.domain.schemas.user import CheckEmailResponse, RegisterUserRequest
from src.services.token_service import TokenService
from src.services.user_mei_service import UserMEIService

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo MEI",
    description="Cria cadastro completo de MEI e retorna tokens de autenticação.",
)
async def register_mei(
    body: RegisterUserRequest,
    user_mei_service: UserMEIService = Depends(get_user_mei_service),
    token_service: TokenService = Depends(get_token_service),
) -> TokenResponse:
    """
    Registra um novo usuário MEI no sistema.

    Args:
        body: Dados completos do MEI

    Returns:
        Tokens de acesso e renovação

    Raises:
        HTTPException 409: Se e-mail ou CNPJ já cadastrado
        HTTPException 422: Se dados inválidos
    """
    user = user_mei_service.register_mei(
        name=body.name,
        email=body.email,
        password=body.password,
        cnpj=body.cnpj,
        interested_state_ids=body.interested_state_ids,
        cnae_ids=body.cnae_ids,
    )

    user_id = user["id"]

    return TokenResponse(
        access_token=token_service.create_access_token(user_id),
        refresh_token=token_service.create_refresh_token(user_id),
    )


@router.get(
    "/check-email",
    response_model=CheckEmailResponse,
    summary="Verificar disponibilidade de e-mail",
    description="Verifica se um e-mail já está cadastrado no sistema.",
)
async def check_email_availability(
    email: str = Query(..., description="E-mail a ser verificado"),
    user_mei_service: UserMEIService = Depends(get_user_mei_service),
) -> CheckEmailResponse:
    """
    Verifica se um e-mail está disponível para cadastro.

    Args:
        email: E-mail a ser verificado

    Returns:
        Indicação se o e-mail está disponível
    """
    available = user_mei_service.check_email_availability(email)
    return CheckEmailResponse(available=available)
