"""Service para gerenciamento de perfil de usuário."""

from fastapi import HTTPException, status

from src.core.logging import get_logger
from src.domain.entities.user import User
from src.integrations.opencnpj import OpenCNPJClient
from src.repositories.cnae_repository import CNAERepository
from src.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserProfileService:
    """Service para operações de perfil de usuário."""

    def __init__(
        self,
        cnae_repository: CNAERepository,
        opencnpj_client: OpenCNPJClient,
        user_repository: UserRepository,
    ):
        self.cnae_repository = cnae_repository
        self.opencnpj_client = opencnpj_client
        self.user_repository = user_repository

    def get_user_profile(self, user: User) -> dict:
        """Retorna perfil completo do usuário."""
        profile: dict = {
            "name": user.name,
            "email": user.email,
            "cnpj": user.cnpj,
            "company_name": user.company_name,
            "primary_cnae": None,
            "secondary_cnaes": [],
            "interested_states": [],
        }

        user_cnaes = self.cnae_repository.get_user_cnaes(user.id)

        if user_cnaes:
            profile["primary_cnae"] = {
                "id": user_cnaes[0]["id"],
                "description": user_cnaes[0]["title"],
            }
            if len(user_cnaes) > 1:
                profile["secondary_cnaes"] = [
                    {"id": cnae["id"], "description": cnae["title"]}
                    for cnae in user_cnaes[1:]
                ]

        raw_state_siglas = self.user_repository.get_interested_states(user.id)
        profile["interested_states"] = [{"sigla": s} for s in raw_state_siglas]

        return profile

    async def update_user_cnpj(self, user: User, cnpj: str) -> dict:
        """Atualiza CNPJ do usuário e sincroniza CNAEs via CNPJA.

        Raises:
            HTTPException 404: Se CNPJ não encontrado na CNPJA
            HTTPException 500: Se erro ao buscar dados do CNPJ
        """
        try:
            cnpj_data = await self.opencnpj_client.get_cnpj_data(cnpj)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao buscar dados do CNPJ",
            ) from e
        if not cnpj_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CNPJ não encontrado na base da Receita Federal",
            )

        company_name: str | None = (
            cnpj_data.get("company", {}).get("name")
            or cnpj_data.get("company", {}).get("razao_social")
            or cnpj_data.get("razao_social")
        )

        cnaes_data = self.opencnpj_client.parse_cnaes_from_data(cnpj_data)

        cnaes_to_upsert = []
        cnae_ids = []

        if cnaes_data["primary"]:
            primary = cnaes_data["primary"]
            cnaes_to_upsert.append({"id": primary["id"], "title": primary["title"]})
            cnae_ids.append(primary["id"])

        for secondary in cnaes_data["secondary"]:
            cnaes_to_upsert.append({"id": secondary["id"], "title": secondary["title"]})
            cnae_ids.append(secondary["id"])

        if cnaes_to_upsert:
            self.cnae_repository.upsert_many(cnaes_to_upsert)
            self.cnae_repository.link_user_cnaes(user.id, cnae_ids)

        self.user_repository.update_cnpj(user.id, cnpj, company_name=company_name)
        user.cnpj = cnpj
        user.company_name = company_name

        return self.get_user_profile(user)

    def update_user_profile(
        self,
        user: User,
        name: str | None = None,
        interested_state_siglas: list[str] | None = None,
        cnae_ids: list[str] | None = None,
    ) -> dict:
        """Atualiza perfil do usuário (nome, estados, CNAEs)."""
        if name is not None:
            self.user_repository.update_profile(user.id, name=name)
            user.name = name

        if interested_state_siglas is not None:
            self.user_repository.link_interested_states(user.id,
                                                        interested_state_siglas)

        if cnae_ids is not None:
            self.cnae_repository.link_user_cnaes(user.id, cnae_ids)

        logger.info(
            "Perfil do usuário atualizado",
            extra_fields={
                "user_id": user.id,
                "updated_name": name is not None,
                "updated_states": interested_state_siglas is not None,
                "updated_cnaes": cnae_ids is not None,
            },
        )

        return self.get_user_profile(user)

    async def refresh_user_cnaes(self, user: User) -> dict:
        """Reexecuta consulta na Receita Federal para atualizar CNAEs do usuário."""
        if not user.cnpj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário não possui CNPJ cadastrado",
            )

        try:
            cnpj_data = await self.opencnpj_client.get_cnpj_data(user.cnpj)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao buscar dados do CNPJ",
            ) from e

        if not cnpj_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CNPJ não encontrado na base da Receita Federal",
            )

        cnaes_data = self.opencnpj_client.parse_cnaes_from_data(cnpj_data)

        cnaes_to_upsert = []
        cnae_ids = []

        if cnaes_data["primary"]:
            primary = cnaes_data["primary"]
            cnaes_to_upsert.append({"id": primary["id"], "title": primary["title"]})
            cnae_ids.append(primary["id"])

        for secondary in cnaes_data["secondary"]:
            cnaes_to_upsert.append({"id": secondary["id"], "title": secondary["title"]})
            cnae_ids.append(secondary["id"])

        if cnaes_to_upsert:
            self.cnae_repository.upsert_many(cnaes_to_upsert)
            self.cnae_repository.link_user_cnaes(user.id, cnae_ids)

        logger.info(
            "CNAEs do usuário sincronizados com Receita Federal",
            extra_fields={"user_id": user.id, "cnpj": user.cnpj[:8] + "****"},
        )

        return self.get_user_profile(user)

    def anonymize_user(self, user: User) -> dict:
        """Anonimiza usuário em conformidade com LGPD Art. 18."""
        anonymized_user = self.user_repository.anonymize_user(user.id)

        logger.info(
            "Usuário anonimizado (LGPD compliance)",
            extra_fields={
                "user_id": user.id,
                "anonymized_at": anonymized_user["anonymized_at"],
            },
        )

        return anonymized_user

