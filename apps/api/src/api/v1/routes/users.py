"""Rotas para gerenciamento de usuários."""

from fastapi import APIRouter, Depends, Query, status

from src.core.dependencies import (
    get_current_user,
    get_token_service,
    get_user_mei_service,
    get_user_profile_service,
)
from src.domain.entities.user import User
from src.domain.schemas.auth import TokenResponse
from src.domain.schemas.user import (
    CheckEmailResponse,
    RegisterUserRequest,
    UpdateUserCNPJRequest,
    UserProfileResponse,
)
from src.services.token_service import TokenService
from src.services.user_mei_service import UserMEIService
from src.services.user_profile_service import UserProfileService

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


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Obter perfil do usuário autenticado",
    description="""
    Retorna informações completas do usuário logado, incluindo dados da empresa e CNAEs.
    """
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    profile_service: UserProfileService = Depends(get_user_profile_service),
) -> UserProfileResponse:
    """
    Retorna perfil completo do usuário autenticado.

    Inclui:
    - Nome do usuário
    - Nome da empresa (razão social via CNPJ)
    - CNPJ
    - Email
    - CNAE principal
    - CNAEs secundários

    Requer autenticação via Bearer token.
    """
    profile = profile_service.get_user_profile(current_user)
    return UserProfileResponse(**profile)


@router.patch(
    "/me/cnpj",
    response_model=UserProfileResponse,
    summary="Atualizar CNPJ e sincronizar CNAEs",
    description="Atualiza o CNPJ do usuário e busca CNAEs automaticamente via CNPJA.",
)
async def update_user_cnpj(
    body: UpdateUserCNPJRequest,
    current_user: User = Depends(get_current_user),
    profile_service: UserProfileService = Depends(get_user_profile_service),
) -> UserProfileResponse:
    """
    Atualiza CNPJ do usuário e sincroniza CNAEs.

    Validações:
    - Verifica se o CNPJ já não está cadastrado para o usuário
    - Verifica se o CNPJ não pertence a outro usuário
    - Busca dados do CNPJ na base da Receita Federal (via CNPJA)
    - Atualiza CNAEs automaticamente

    Args:
        body: CNPJ a ser cadastrado

    Returns:
        Perfil atualizado com CNPJ e CNAEs

    Raises:
        HTTPException 400: Se CNPJ já cadastrado para o usuário
        HTTPException 404: Se CNPJ não encontrado
        HTTPException 409: Se CNPJ já pertence a outro usuário

    Requer autenticação via Bearer token.
    """
    profile = await profile_service.update_user_cnpj(current_user, body.cnpj)
    return UserProfileResponse(**profile)
