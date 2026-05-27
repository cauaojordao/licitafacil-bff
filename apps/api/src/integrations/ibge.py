"""Integração com API do IBGE para dados de localidades."""

import httpx

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class IBGEClient:
    """Cliente para integração com API do IBGE."""

    def __init__(self) -> None:
        """Inicializa o cliente HTTP."""
        self.base_url = settings.IBGE_API_URL
        self.timeout = 10.0

    async def get_states(self) -> list[dict[str, str]]:
        """
        Busca lista de todos os estados brasileiros.

        Returns:
            Lista de estados com id, sigla e nome

        Raises:
            httpx.HTTPError: Se houver erro na requisição
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/estados", params={"orderBy": "nome"}
                )
                response.raise_for_status()

                estados = response.json()

                return [
                    {
                        "id": str(estado["id"]),
                        "sigla": estado["sigla"],
                        "nome": estado["nome"],
                    }
                    for estado in estados
                ]
        except httpx.HTTPError as e:
            logger.error(
                "Erro ao buscar estados do IBGE",
                extra_fields={"error": str(e)},
            )
            raise

    async def get_state_by_id(self, state_id: str) -> dict[str, str] | None:
        """
        Busca dados de um estado específico pelo ID.

        Args:
            state_id: ID do estado no IBGE

        Returns:
            Dados do estado ou None se não encontrado

        Raises:
            httpx.HTTPError: Se houver erro na requisição
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/estados/{state_id}")

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                estado = response.json()

                return {
                    "id": str(estado["id"]),
                    "sigla": estado["sigla"],
                    "nome": estado["nome"],
                }
        except httpx.HTTPError as e:
            logger.error(
                "Erro ao buscar estado do IBGE",
                extra_fields={"state_id": state_id, "error": str(e)},
            )
            raise

    async def get_cities_by_state(self, state_id: str) -> list[dict[str, str]]:
        """
        Busca lista de municípios de um estado.

        Args:
            state_id: ID do estado no IBGE

        Returns:
            Lista de municípios com id e nome

        Raises:
            httpx.HTTPError: Se houver erro na requisição
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/estados/{state_id}/municipios",
                    params={"orderBy": "nome"},
                )
                response.raise_for_status()

                municipios = response.json()

                return [
                    {
                        "id": str(municipio["id"]),
                        "nome": municipio["nome"],
                    }
                    for municipio in municipios
                ]
        except httpx.HTTPError as e:
            logger.error(
                "Erro ao buscar municípios do IBGE",
                extra_fields={"state_id": state_id, "error": str(e)},
            )
            raise


ibge_client = IBGEClient()
