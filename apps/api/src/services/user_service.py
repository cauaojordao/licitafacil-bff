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
        return self.user_repository.create(name, email, password_hash)

    def authenticate_user(self, email: str, password: str) -> dict:
        user = self.user_repository.find_by_email(email)

        if not user or not verify_password(password, user["password_hash"]):
            logger.warning("Tentativa de login com credenciais inválidas")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos",
            )

        return user

    def get_user_by_id(self, user_id: str) -> dict | None:
        return self.user_repository.find_by_id(user_id)

    def update_user_password(self, user_id: str, new_password: str) -> None:
        password_hash = hash_password(new_password)
        self.user_repository.update_password(user_id, password_hash)
