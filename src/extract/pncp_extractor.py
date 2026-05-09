from typing import Any
import requests


class PNCPExtractor:
    """
    Classe responsável por extrair dados da API do PNCP.
    """

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        """
        Inicializa o extrator.

        Args:
            base_url: URL base da API do PNCP.
            timeout: Tempo máximo da requisição em segundos.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_page(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Realiza a consulta de uma página da API do PNCP.

        Args:
            endpoint: Endpoint da API.
            params: Parâmetros de consulta.

        Returns:
            JSON retornado pela API.

        Raises:
            requests.HTTPError: Caso a API retorne erro HTTP.
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def fetch_all(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extrai todos os registros paginados da API.

        Args:
            endpoint: Endpoint da API.
            params: Parâmetros obrigatórios e opcionais da consulta.

        Returns:
            Lista com todos os registros retornados pela API.
        """
        all_records: list[dict[str, Any]] = []
        current_page = 1

        while True:
            page_params = params.copy()
            page_params["pagina"] = current_page

            response_data = self.fetch_page(endpoint=endpoint, params=page_params)

            records = response_data.get("data", [])
            all_records.extend(records)

            remaining_pages = response_data.get("paginasRestantes", 0)

            if remaining_pages == 0:
                break

            current_page += 1

        return all_records