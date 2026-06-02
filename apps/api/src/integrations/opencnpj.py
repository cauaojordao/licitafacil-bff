"""Integração com API OpenCNPJ para consulta de CNPJ."""

from typing import TypedDict

import httpx

from src.core.config import settings
from src.core.logging import get_logger
from src.utils.cnpj import clean_cnpj as _clean_cnpj
from src.utils.cnpj import format_cnpj as _format_cnpj

logger = get_logger(__name__)


class CNAEData(TypedDict):
    """Estrutura de dados de CNAEs (principal e secundários)."""

    primary: dict[str, str] | None
    secondary: list[dict[str, str]]


class OpenCNPJClient:
    """Cliente para integração com API OpenCNPJ."""

    def __init__(self) -> None:
        """Inicializa o cliente HTTP."""
        self.base_url = settings.CNPJA_API_URL
        self.timeout = 15.0

    async def get_cnpj_data(self, cnpj: str) -> dict | None:
        """
        Busca dados completos de um CNPJ.

        Args:
            cnpj: CNPJ com ou sem formatação

        Returns:
            Dados do CNPJ ou None se não encontrado

        Raises:
            httpx.HTTPError: Se houver erro na requisição
            ValueError: Se CNPJ inválido
        """
        cnpj = self.clean_cnpj(cnpj)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/office/{cnpj}",
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 404:
                    logger.info(
                        "CNPJ não encontrado",
                        extra_fields={"cnpj": cnpj[:8] + "****"},
                    )
                    return None

                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(
                "Erro ao consultar CNPJ no OpenCNPJ",
                extra_fields={"cnpj": cnpj[:8] + "****", "error": str(e)},
            )
            raise

    def parse_cnaes_from_data(self, data: dict) -> CNAEData:
        """Extrai CNAEs de um payload de dados de CNPJ já carregado."""
        primary_cnae = None
        secondary_cnaes = []

        if data.get("mainActivity"):
            main = data["mainActivity"]
            primary_cnae = {"id": str(main["id"]), "title": main["text"]}

        for activity in data.get("sideActivities") or []:
            secondary_cnaes.append(
                {"id": str(activity["id"]), "title": activity["text"]}
            )

        return {"primary": primary_cnae, "secondary": secondary_cnaes}

    async def get_cnpj_cnaes(self, cnpj: str) -> CNAEData:
        """Busca CNAEs de um CNPJ (principal e secundários separados)."""
        data = await self.get_cnpj_data(cnpj)

        if not data:
            return {"primary": None, "secondary": []}

        result = self.parse_cnaes_from_data(data)
        total = (1 if result["primary"] else 0) + len(result["secondary"])
        logger.info(
            "CNAEs consultados com sucesso",
            extra_fields={"cnpj": cnpj[:8] + "****", "total_cnaes": total},
        )
        return result

    def format_cnpj(self, cnpj: str) -> str:
        """Formata CNPJ alfanumérico para exibição (XX.XXX.XXX/XXXX-XX)."""
        return _format_cnpj(cnpj)

    def clean_cnpj(self, cnpj: str) -> str:
        """Remove formatação do CNPJ e valida que possui 14 caracteres.

        Raises:
            ValueError: Se o CNPJ não tiver 14 caracteres após limpeza
        """
        return _clean_cnpj(cnpj)
