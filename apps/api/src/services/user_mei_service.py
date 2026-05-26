"""Service para registro e gerenciamento de usuários MEI."""

from fastapi import HTTPException, status

from src.core.logging import get_logger
from src.core.security import hash_password
from src.repositories.cnae_repository import CNAERepository
from src.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserMEIService:
    """Service para operações com usuários MEI."""

    def __init__(
        self,
        user_repository: UserRepository,
        cnae_repository: CNAERepository,
    ):
        """
        Inicializa o service com suas dependências.

        Args:
            user_repository: Repository de usuários
            cnae_repository: Repository de CNAEs
        """
        self.user_repository = user_repository
        self.cnae_repository = cnae_repository

    def register_mei(
        self,
        name: str,
        email: str,
        password: str,
        cnpj: str,
        interested_state_ids: list[str],
        cnae_ids: list[str],
    ) -> dict:
        """
        Registra um novo usuário MEI com cadastro completo.

        Args:
            name: Nome do usuário
            email: E-mail do usuário
            password: Senha em texto plano
            cnpj: CNPJ alfanumérico do MEI (14 caracteres, sem formatação)
            interested_state_ids: IDs IBGE dos estados de interesse
            cnae_ids: Códigos dos CNAEs selecionados

        Returns:
            Dados do usuário criado

        Raises:
            HTTPException: Se email ou CNPJ já cadastrado
        """
        existing_email = self.user_repository.find_by_email(email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado",
            )

        existing_cnpj = self.user_repository.find_by_cnpj(cnpj)
        if existing_cnpj:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="CNPJ já cadastrado",
            )

        password_hash = hash_password(password)
        user = self.user_repository.create_mei(
            name=name,
            email=email,
            password_hash=password_hash,
            cnpj=cnpj,
        )

        user_id = user["id"]

        try:
            # Vincular estados e CNAEs
            self.user_repository.link_interested_states(user_id, interested_state_ids)
            self.cnae_repository.link_user_cnaes(user_id, cnae_ids)

            # Só marca como completo após todos os vínculos
            self.user_repository.mark_registration_complete(user_id)

        except Exception:
            # Se falhar, o usuário fica incompleto (registration_complete=False)
            logger.error(
                "Erro ao vincular dados do MEI",
                extra_fields={"user_id": user_id},
            )
            raise

        logger.info(
            "Usuário MEI registrado com sucesso",
            extra_fields={
                "user_id": user_id,
                "cnpj": cnpj[:8] + "****",
                "states_count": len(interested_state_ids),
                "cnaes_count": len(cnae_ids),
            },
        )

        updated_user = self.user_repository.find_by_id(user_id)
        if not updated_user:
            raise RuntimeError("Failed to reload user after registration")
        return updated_user

    def check_email_availability(self, email: str) -> bool:
        """
        Verifica se um e-mail está disponível.

        Args:
            email: E-mail a ser verificado

        Returns:
            True se disponível, False se já cadastrado
        """
        user = self.user_repository.find_by_email(email)
        return user is None

    def check_cnpj_availability(self, cnpj: str) -> bool:
        """
        Verifica se um CNPJ está disponível.

        Args:
            cnpj: CNPJ alfanumérico a ser verificado (14 caracteres)

        Returns:
            True se disponível, False se já cadastrado
        """
        user = self.user_repository.find_by_cnpj(cnpj)
        return user is None
