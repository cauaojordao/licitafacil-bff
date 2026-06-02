"""Service para registro e gerenciamento de usuários MEI."""

from fastapi import HTTPException, status

from src.core.logging import get_logger
from src.core.security import hash_password
from src.integrations.opencnpj import OpenCNPJClient
from src.repositories.cnae_repository import CNAERepository
from src.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserMEIService:
    """Service para operações com usuários MEI."""

    def __init__(
        self,
        user_repository: UserRepository,
        cnae_repository: CNAERepository,
        opencnpj_client: OpenCNPJClient,
    ):
        """
        Inicializa o service com suas dependências.

        Args:
            user_repository: Repository de usuários
            cnae_repository: Repository de CNAEs
            opencnpj_client: Cliente da API de CNPJ
        """
        self.user_repository = user_repository
        self.cnae_repository = cnae_repository
        self.opencnpj_client = opencnpj_client

    async def register_mei(
        self,
        name: str,
        email: str,
        password: str,
        cnpj: str,
        interested_state_siglas: list[str],
        cnae_ids: list[str],
    ) -> dict:
        """
        Registra um novo usuário MEI com cadastro completo.

        Args:
            name: Nome do usuário
            email: E-mail do usuário
            password: Senha em texto plano
            cnpj: CNPJ alfanumérico do MEI (14 caracteres, sem formatação)
            interested_state_siglas: Siglas das UFs de interesse (ex: ["PE", "SP"])
            cnae_ids: Códigos dos CNAEs selecionados

        Returns:
            Dados do usuário criado

        Raises:
            HTTPException: Se e-mail já cadastrado
        """
        existing_email = self.user_repository.find_by_email(email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado",
            )

        # Busca razão social e CNAEs na Receita Federal
        company_name: str | None = None
        api_cnaes: list[dict] = []

        try:
            cnpj_data = await self.opencnpj_client.get_cnpj_data(cnpj)
            if cnpj_data:
                company_name = (
                    cnpj_data.get("company", {}).get("name")
                    or cnpj_data.get("company", {}).get("razao_social")
                    or cnpj_data.get("razao_social")
                )
                cnaes_parsed = self.opencnpj_client.parse_cnaes_from_data(cnpj_data)
                if cnaes_parsed["primary"]:
                    api_cnaes.append(cnaes_parsed["primary"])
                api_cnaes.extend(cnaes_parsed["secondary"])
        except Exception:
            logger.warning(
                "Não foi possível buscar dados do CNPJ na API, continuando registro",
                extra_fields={"cnpj": cnpj[:8] + "****"},
            )

        password_hash = hash_password(password)
        user = self.user_repository.create_mei(
            name=name,
            email=email,
            password_hash=password_hash,
            cnpj=cnpj,
            company_name=company_name,
        )

        user_id = user["id"]

        try:
            api_cnae_ids = {c["id"] for c in api_cnaes}
            if api_cnaes:
                self.cnae_repository.upsert_many(api_cnaes)

            missing_cnae_ids = [cid for cid in cnae_ids if cid not in api_cnae_ids]
            if missing_cnae_ids:
                self.cnae_repository.upsert_many(
                    [{"id": cid, "title": cid} for cid in missing_cnae_ids]
                )

            self.user_repository.link_interested_states(
                user_id, interested_state_siglas
            )
            self.cnae_repository.link_user_cnaes(user_id, cnae_ids)
            self.user_repository.mark_registration_complete(user_id)

        except Exception:
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
                "company_name": company_name,
                "states_count": len(interested_state_siglas),
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
