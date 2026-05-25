"""Dependências do FastAPI para injeção em rotas."""

from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from supabase import Client

from src.db.session import get_supabase
from src.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.token_service import TokenService
from src.services.user_service import UserService

bearer_scheme = HTTPBearer()


# Dependências de Repositories


def get_user_repository(db: Client = Depends(get_supabase)) -> UserRepository:
    """
    Fornece instância do UserRepository.

    Args:
        db: Cliente do banco de dados

    Returns:
        Instância configurada do UserRepository
    """
    return UserRepository(db)


def get_password_reset_repository(
    db: Client = Depends(get_supabase),
) -> PasswordResetTokenRepository:
    """
    Fornece instância do PasswordResetTokenRepository.

    Args:
        db: Cliente do banco de dados

    Returns:
        Instância configurada do PasswordResetTokenRepository
    """
    return PasswordResetTokenRepository(db)


# Dependências de Services


@lru_cache
def get_token_service() -> TokenService:
    """
    Fornece instância singleton do TokenService.

    Returns:
        Instância do TokenService
    """
    return TokenService()


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    """
    Fornece instância do UserService.

    Args:
        user_repository: Repository de usuários

    Returns:
        Instância configurada do UserService
    """
    return UserService(user_repository)


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    password_reset_repository: PasswordResetTokenRepository = Depends(
        get_password_reset_repository
    ),
) -> AuthService:
    """
    Fornece instância do AuthService.

    Args:
        user_service: Service de usuários
        token_service: Service de tokens
        password_reset_repository: Repository de tokens de reset

    Returns:
        Instância configurada do AuthService
    """
    return AuthService(user_service, token_service, password_reset_repository)


# Dependência de autenticação


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    token_service: TokenService = Depends(get_token_service),
) -> str:
    """
    Dependência para validar access token e retornar user_id.

    Args:
        credentials: Credenciais de autenticação do header
        token_service: Service de tokens

    Returns:
        ID do usuário autenticado

    Raises:
        HTTPException 401: Se o token for inválido ou expirado
    """
    token = credentials.credentials
    try:
        user_id = token_service.validate_access_token(token)
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return user_id
