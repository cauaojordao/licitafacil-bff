"""Dependências do FastAPI para injeção em rotas."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from supabase import Client

from src.db.session import get_supabase
from src.domain.entities.user import User
from src.integrations.ibge import IBGEClient
from src.integrations.ibge import ibge_client as _ibge_singleton
from src.integrations.opencnpj import OpenCNPJClient
from src.repositories.cnae_repository import CNAERepository
from src.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.token_service import TokenService
from src.services.user_mei_service import UserMEIService
from src.services.user_profile_service import UserProfileService
from src.services.user_service import UserService

bearer_scheme = HTTPBearer()


def get_supabase_client(db: Client = Depends(get_supabase)) -> Client:
    """Retorna o cliente Supabase para injeção de dependência."""
    return db


def get_user_repository(db: Client = Depends(get_supabase)) -> UserRepository:
    return UserRepository(db)


def get_password_reset_repository(
    db: Client = Depends(get_supabase),
) -> PasswordResetTokenRepository:
    return PasswordResetTokenRepository(db)


def get_cnae_repository(db: Client = Depends(get_supabase)) -> CNAERepository:
    return CNAERepository(db)


def get_token_service() -> TokenService:
    return TokenService()


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repository)


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    password_reset_repository: PasswordResetTokenRepository = Depends(
        get_password_reset_repository
    ),
) -> AuthService:
    return AuthService(user_service, token_service, password_reset_repository)


def get_opencnpj_client() -> OpenCNPJClient:
    """Retorna instância do cliente OpenCNPJ."""
    return OpenCNPJClient()


def get_ibge_client() -> IBGEClient:
    """Retorna o singleton do cliente IBGE."""
    return _ibge_singleton


def get_user_mei_service(
    user_repository: UserRepository = Depends(get_user_repository),
    cnae_repository: CNAERepository = Depends(get_cnae_repository),
    opencnpj_client: OpenCNPJClient = Depends(get_opencnpj_client),
) -> UserMEIService:
    return UserMEIService(user_repository, cnae_repository, opencnpj_client)


def get_user_profile_service(
    cnae_repository: CNAERepository = Depends(get_cnae_repository),
    opencnpj_client: OpenCNPJClient = Depends(get_opencnpj_client),
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserProfileService:
    """Retorna instância do UserProfileService."""
    return UserProfileService(cnae_repository, opencnpj_client, user_repository)


# Dependência de autenticação


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    token_service: TokenService = Depends(get_token_service),
    user_repository: UserRepository = Depends(get_user_repository),
) -> "User":
    """
    Dependência para validar access token e retornar usuário completo.

    Args:
        credentials: Credenciais de autenticação do header
        token_service: Service de tokens
        user_repository: Repository de usuários

    Returns:
        Objeto User completo

    Raises:
        HTTPException 401: Se o token for inválido ou expirado
    """
    from src.domain.entities.user import User

    token = credentials.credentials
    try:
        user_id = token_service.validate_access_token(token)
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user_data = user_repository.find_by_id(user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(**user_data)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
    token_service: TokenService = Depends(get_token_service),
    user_repository: UserRepository = Depends(get_user_repository),
) -> "User | None":
    """
    Dependência opcional para validar access token.

    Retorna None se não houver token, ao invés de lançar erro 401.

    Args:
        credentials: Credenciais de autenticação do header (opcional)
        token_service: Service de tokens
        user_repository: Repository de usuários

    Returns:
        Objeto User completo ou None se não autenticado
    """
    from src.domain.entities.user import User

    if not credentials or not credentials.credentials:
        return None

    token = credentials.credentials
    try:
        user_id = token_service.validate_access_token(token)
    except (JWTError, KeyError, ValueError):
        return None

    user_data = user_repository.find_by_id(user_id)
    if not user_data:
        return None

    return User(**user_data)
