"""Rotas para consulta de CNPJ e CNAEs."""

from fastapi import APIRouter, HTTPException, status

from src.domain.schemas.user import CNAEResponse, CNPJCNAEsResponse
from src.integrations.opencnpj import opencnpj_client

router = APIRouter()


@router.get(
    "/{cnpj}/cnaes",
    response_model=CNPJCNAEsResponse,
    summary="Consultar CNAEs de um CNPJ",
    description="Busca lista de CNAEs de um CNPJ via OpenCNPJ.",
)
async def get_cnpj_cnaes(cnpj: str) -> CNPJCNAEsResponse:
    """
    Consulta CNAEs de um CNPJ na OpenCNPJ API.

    Args:
        cnpj: CNPJ alfanumérico com 14 caracteres (pode conter formatação)

    Returns:
        Lista de CNAEs do CNPJ

    Raises:
        HTTPException 400: Se CNPJ inválido
        HTTPException 404: Se CNPJ não encontrado
        HTTPException 500: Se erro na consulta
    """

    cnpj_limpo = opencnpj_client.clean_cnpj(cnpj)

    try:
        data = await opencnpj_client.get_cnpj_data(cnpj_limpo)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CNPJ não encontrado",
            )

        cnaes_data = await opencnpj_client.get_cnpj_cnaes(cnpj_limpo)

        razao_social = None
        if "company" in data and data["company"]:
            razao_social = data["company"].get("name")

        primary_cnae_dict = cnaes_data["primary"]
        secondary_cnaes_data = cnaes_data["secondary"]

        return CNPJCNAEsResponse(
            cnpj=opencnpj_client.format_cnpj(cnpj_limpo),
            razao_social=razao_social,
            primary_cnae=CNAEResponse(**primary_cnae_dict)
            if primary_cnae_dict and isinstance(primary_cnae_dict, dict)
            else None,
            secondary_cnaes=[CNAEResponse(**cnae) for cnae in secondary_cnaes_data]
            if isinstance(secondary_cnaes_data, list)
            else [],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao consultar CNPJ",
        ) from e
