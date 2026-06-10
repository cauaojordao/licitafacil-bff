"""Service para gerenciamento de usuários."""

from fastapi import HTTPException, status

from src.core.logging import get_logger
from src.core.security import hash_password, verify_password
from src.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserService:
    """Service para operações de lógica de negócio relacionadas a usuários."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register_user(self, name: str, email: str, password: str) -> dict:
        existing = self.user_repository.find_by_email(email)
        if existing:
            logger.warning("Tentativa de registro com email já cadastrado")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado",
            )

        password_hash = hash_password(password)
        return self.user_repository.create_user(name, email, password_hash)

    def authenticate_user(self, email: str, password: str) -> dict:
        user = self.user_repository.find_by_email(email)

        if not user:
            logger.warning("Tentativa de login com email não cadastrado")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos",
            )

        if self.user_repository.is_account_locked(user):
            logger.warning(
                "Tentativa de login em conta bloqueada",
                extra_fields={"user_id": user["id"]},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conta bloqueada temporariamente por excesso de tentativas. "
                "Tente novamente em alguns minutos.",
            )

        if not verify_password(password, user["password_hash"]):
            self.user_repository.increment_failed_attempts(user["id"])
            logger.warning(
                "Tentativa de login com credenciais inválidas",
                extra_fields={"user_id": user["id"]},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos",
            )

        self.user_repository.reset_failed_attempts(user["id"])
        return user

    def get_user_by_id(self, user_id: str) -> dict | None:
        return self.user_repository.find_by_id(user_id)

    def update_user_password(self, user_id: str, new_password: str) -> None:
        password_hash = hash_password(new_password)
        self.user_repository.update_password(user_id, password_hash)
