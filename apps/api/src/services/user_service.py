"""Service para gerenciamento de usuários."""


from fastapi import HTTPException, status

from src.core.security import hash_password, verify_password
from src.repositories.user_repository import UserRepository


class UserService:
    """Service para operações de lógica de negócio relacionadas a usuários."""

    def __init__(self, user_repository: UserRepository):
        """
        Inicializa o service com suas dependências.

        Args:
            user_repository: Repository de usuários
        """
        self.user_repository = user_repository

    def register_user(self, name: str, email: str, password: str) -> dict:
        """
        Registra um novo usuário no sistema.

        Args:
            name: Nome do usuário
            email: E-mail do usuário
            password: Senha em texto plano

        Returns:
            Dados do usuário criado

        Raises:
            HTTPException: Se o e-mail já estiver cadastrado
        """
        existing = self.user_repository.find_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado",
            )

        password_hash = hash_password(password)
        return self.user_repository.create(name, email, password_hash)

    def authenticate_user(self, email: str, password: str) -> dict:
        """
        Autentica um usuário verificando email e senha.

        Args:
            email: E-mail do usuário
            password: Senha em texto plano

        Returns:
            Dados do usuário autenticado

        Raises:
            HTTPException: Se credenciais forem inválidas
        """
        user = self.user_repository.find_by_email(email)

        # Mensagem genérica para não revelar se o e-mail existe
        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos",
            )

        return user

    def get_user_by_id(self, user_id: str) -> dict | None:
        """
        Busca um usuário pelo ID.

        Args:
            user_id: ID do usuário

        Returns:
            Dados do usuário ou None se não encontrado
        """
        return self.user_repository.find_by_id(user_id)

    def update_user_password(self, user_id: str, new_password: str) -> None:
        """
        Atualiza a senha de um usuário.

        Args:
            user_id: ID do usuário
            new_password: Nova senha em texto plano
        """
        password_hash = hash_password(new_password)
        self.user_repository.update_password(user_id, password_hash)
